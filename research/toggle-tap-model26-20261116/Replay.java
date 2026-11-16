import com.lingion.sleepy.ui.component.liquidglass.ActiveFrame;
import com.lingion.sleepy.ui.component.liquidglass.GlassControlMotion;
import com.lingion.sleepy.ui.component.liquidglass.GlassControlMotionKt;
import com.lingion.sleepy.ui.component.liquidglass.GlassControlMotionSpec;
import com.lingion.sleepy.ui.component.liquidglass.TimedGlassControlMotion;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** External source-file launcher; no reimplementation of runtime motion. */
class Replay {
    static List<Map<String,String>> read(Path path) throws Exception {
        List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        String[] columns = lines.get(0).split("\t", -1);
        List<Map<String,String>> rows = new ArrayList<>();
        for (String line : lines.subList(1, lines.size())) {
            String[] values = line.split("\t", -1);
            if (values.length != columns.length) throw new IllegalArgumentException("TSV field count: " + path);
            Map<String,String> row = new LinkedHashMap<>();
            for (int i = 0; i < columns.length; i++) row.put(columns[i], values[i]);
            rows.add(row);
        }
        return rows;
    }
    static double number(Map<String,String> row, String key) { return Double.parseDouble(row.get(key)); }
    static long integer(Map<String,String> row, String key) { return Long.parseLong(row.get(key)); }
    static List<Map<String,String>> matching(List<Map<String,String>> rows, String segment) {
        List<Map<String,String>> selected = new ArrayList<>();
        for (Map<String,String> row : rows) if (segment.equals(row.get("segment"))) selected.add(row);
        return selected;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("prepared-dir output.csv");
        Path prepared = Path.of(args[0]);
        List<Map<String,String>> segments = read(prepared.resolve("segments.tsv"));
        List<Map<String,String>> events = read(prepared.resolve("events.tsv"));
        List<Map<String,String>> frames = read(prepared.resolve("frames.tsv"));
        List<String> nativeColumns = new ArrayList<>(frames.get(0).keySet());
        List<String> modelColumns = List.of("model_position", "model_geometry_lift", "model_lift",
            "model_stretch", "model_local_base_w", "model_local_base_h", "model_draw_w", "model_draw_h",
            "model_center_delta", "native_center_delta", "error_base_w", "error_base_h",
            "error_draw_w", "error_draw_h", "error_center_delta", "previous_model_frame_nanos",
            "model_frame_advanced", "begin_applied", "events_injected");
        int total = 0;
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(Path.of(args[1]), StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE))) {
            out.println(String.join(",", nativeColumns) + "," + String.join(",", modelColumns));
            for (Map<String,String> segment : segments) {
                String id = segment.get("segment");
                float initial = (float) number(segment, "initial");
                float target = (float) number(segment, "target");
                double baselineCenter = number(segment, "baseline_world_center");
                TimedGlassControlMotion driver = new TimedGlassControlMotion(initial,
                    GlassControlMotionSpec.Companion.getNative(), 22f, true);
                List<Map<String,String>> inputs = matching(events, id);
                int next = 0;
                Long epoch = null, previous = null;
                for (Map<String,String> frame : matching(frames, id)) {
                    long time = integer(frame, "replay_nanos");
                    int injected = 0;
                    while (next < inputs.size() && integer(inputs.get(next), "received_nanos") <= time) {
                        Map<String,String> input = inputs.get(next++);
                        long received = integer(input, "received_nanos");
                        long sample = integer(input, "sample_millis");
                        if ("0".equals(input.get("phase"))) {
                            // Same ordinary pointer-DOWN contract as GlassSwitch.
                            epoch = driver.begin(true, true, received, sample);
                            if (epoch == null) throw new IllegalStateException("Rejected DOWN");
                        } else if (epoch == null || !driver.release(epoch, target, true, received, sample)) {
                            throw new IllegalStateException("Rejected UP");
                        }
                        injected++;
                    }
                    boolean advanced = driver.needsFrame();
                    Long usedPrevious = advanced ? previous : null;
                    if (advanced) driver.advanceFrame(new ActiveFrame(time, usedPrevious), 1f);
                    // The real active loop drops its previous timestamp while idle.
                    previous = advanced && driver.needsFrame() ? time : null;
                    GlassControlMotion motion = driver.getMotion();
                    float g = motion.getGeometryLift();
                    float stretch = motion.getStretch() * .25f;
                    float baseW = 37f + 21f * g, baseH = 24f + (43f/3f) * g;
                    float drawW = GlassControlMotionKt.glassLensWidth(baseW, stretch);
                    float drawH = GlassControlMotionKt.glassLensHeight(baseH, stretch, 24f + 13f * g);
                    double modelDelta = (motion.getPosition().getValue() - initial) * 22.0;
                    double nativeDelta = number(frame, "x") + number(frame, "w") / 2 - baselineCenter;
                    List<String> row = new ArrayList<>(frame.values());
                    for (Object v : List.of(motion.getPosition().getValue(), g, motion.getLift(), stretch,
                            baseW, baseH, drawW, drawH, modelDelta, nativeDelta,
                            baseW-number(frame,"boundsW"), baseH-number(frame,"boundsH"),
                            drawW-number(frame,"boundsW"), drawH-number(frame,"boundsH"), modelDelta-nativeDelta,
                            usedPrevious == null ? "" : usedPrevious, advanced,
                            driver.getAppliedPressEpoch() != null, injected)) row.add(v.toString());
                    for (String value : row) if (value.contains(",") || value.contains("\n"))
                        throw new IllegalArgumentException("Unexpected CSV escaping requirement");
                    out.println(String.join(",", row));
                    total++;
                }
                if (next != inputs.size()) throw new IllegalStateException("Undelivered inputs");
            }
            if (total != 838 || out.checkError()) throw new IllegalStateException("Incomplete replay export");
        }
        System.out.println("Exported " + total + " core-model diagnostic frames; no GPU/optical acceptance");
    }
}
