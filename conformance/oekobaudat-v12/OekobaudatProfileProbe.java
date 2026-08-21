package proofgrid.v08;

import com.okworx.ilcd.validation.IDatasetsValidator;
import com.okworx.ilcd.validation.Validator;
import com.okworx.ilcd.validation.ValidatorChain;
import com.okworx.ilcd.validation.events.EventsList;
import com.okworx.ilcd.validation.events.IValidationEvent;
import com.okworx.ilcd.validation.profile.Profile;
import com.okworx.ilcd.validation.profile.ProfileManager;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Research-only headless probe for the official ilcd-validation library and
 * exact ÖKOBAUDAT profile JAR. This class does not reimplement profile rules.
 */
public final class OekobaudatProfileProbe {
    private OekobaudatProfileProbe() {}

    private static String json(String value) {
        if (value == null) return "null";
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '\\': b.append("\\\\"); break;
                case '"': b.append("\\\""); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) b.append(String.format("\\u%04x", (int)c));
                    else b.append(c);
            }
        }
        return b.append('"').toString();
    }

    private static String ref(IValidationEvent event) {
        return event.getReference() == null ? null : String.valueOf(event.getReference());
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 4) {
            System.err.println("usage: OekobaudatProfileProbe PROFILE_JAR DATASET_PATH OUTPUT_JSON LABEL");
            System.exit(64);
        }
        File profileJar = new File(args[0]).getCanonicalFile();
        File dataset = new File(args[1]).getCanonicalFile();
        File output = new File(args[2]).getCanonicalFile();
        String label = args[3];

        if (!profileJar.isFile()) throw new IllegalArgumentException("profile JAR not found: " + profileJar);
        if (!dataset.exists()) throw new IllegalArgumentException("dataset path not found: " + dataset);

        File cache = new File(output.getParentFile(), "profile-cache-" + Math.abs(label.hashCode()));
        new ProfileManager.ProfileManagerBuilder()
                .cacheDir(cache)
                .registerDefaultProfiles(false, false)
                .build();

        ProfileManager manager = ProfileManager.getInstance();
        URL profileUrl = profileJar.toURI().toURL();
        Profile profile = manager.registerProfile(profileUrl);

        ValidatorChain chain = new ValidatorChain("ProofGrid v0.8 official profile probe");
        chain.setProfile(profile);
        chain.initPresetValidators();
        chain.setBatchMode(false);

        List<String> validators = new ArrayList<>();
        for (IDatasetsValidator validator : chain.getValidators()) {
            validators.add(validator == null ? "null" : validator.getAspectName());
        }

        EventsList events = Validator.validate(dataset, chain);

        output.getParentFile().mkdirs();
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(output), StandardCharsets.UTF_8))) {
            w.println("{");
            w.println("  \"label\": " + json(label) + ",");
            w.println("  \"dataset_path\": " + json(dataset.getPath()) + ",");
            w.println("  \"profile_jar\": " + json(profileJar.getPath()) + ",");
            w.println("  \"profile_name\": " + json(profile.getName()) + ",");
            w.println("  \"profile_version\": " + json(profile.getVersion()) + ",");
            w.println("  \"profile_coordinates\": " + json(String.valueOf(profile.getMavenCoordinates())) + ",");
            w.println("  \"active_aspects\": " + json(profile.getActiveAspects()) + ",");
            w.println("  \"supported_aspects\": " + json(profile.getSupportedAspects()) + ",");
            w.print("  \"validators\": [");
            for (int i = 0; i < validators.size(); i++) {
                if (i > 0) w.print(", ");
                w.print(json(validators.get(i)));
            }
            w.println("],");
            w.println("  \"is_positive\": " + events.isPositive() + ",");
            w.println("  \"has_errors\": " + events.hasErrors() + ",");
            w.println("  \"has_warnings\": " + events.hasWarnings() + ",");
            w.println("  \"error_count\": " + events.getErrorCount() + ",");
            w.println("  \"warning_count\": " + events.getWarningCount() + ",");
            w.println("  \"success_count\": " + events.getSuccessCount() + ",");
            w.println("  \"event_count\": " + events.size() + ",");
            w.println("  \"events\": [");
            List<IValidationEvent> all = events.getEvents();
            for (int i = 0; i < all.size(); i++) {
                IValidationEvent e = all.get(i);
                w.println("    {");
                w.println("      \"severity\": " + json(String.valueOf(e.getSeverity())) + ",");
                w.println("      \"type\": " + json(String.valueOf(e.getType())) + ",");
                w.println("      \"aspect\": " + json(e.getAspect()) + ",");
                w.println("      \"aspect_description\": " + json(e.getAspectDescription()) + ",");
                w.println("      \"message\": " + json(e.getMessage()) + ",");
                w.println("      \"alt_message\": " + json(e.getAltMessage()) + ",");
                w.println("      \"reference\": " + json(ref(e)));
                w.print("    }");
                if (i + 1 < all.size()) w.print(',');
                w.println();
            }
            w.println("  ]");
            w.println("}");
        }

        System.out.printf("%s: positive=%s errors=%s warnings=%s events=%s%n",
                label, events.isPositive(), events.getErrorCount(), events.getWarningCount(), events.size());
    }
}
