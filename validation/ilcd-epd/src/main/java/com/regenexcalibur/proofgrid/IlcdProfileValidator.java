package com.regenexcalibur.proofgrid;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.jar.Attributes;
import java.util.jar.JarFile;

import com.fasterxml.jackson.databind.MapperFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.okworx.ilcd.validation.SchemaValidator;
import com.okworx.ilcd.validation.ValidatorChain;
import com.okworx.ilcd.validation.XSLTStylesheetValidator;
import com.okworx.ilcd.validation.events.IValidationEvent;
import com.okworx.ilcd.validation.profile.Profile;
import com.okworx.ilcd.validation.profile.ProfileManager;
import com.okworx.ilcd.validation.reference.IDatasetReference;
import com.okworx.ilcd.validation.reference.ReferenceBuilder;

/**
 * ProofGrid v0.7 technical ILCD+EPD profile validation harness.
 *
 * This harness intentionally delegates schema/profile semantics to the pinned
 * Okworx ILCD validation library and profile. It records technical validation
 * evidence only; it does not claim scientific, programme-operator, regulatory,
 * professional, or certification authority.
 */
public final class IlcdProfileValidator {

  private static final String ENGINE = "RegenExcalibur ProofGrid ILCD+EPD Profile Harness";
  private static final String ENGINE_VERSION = "0.7.0";
  private static final String VALIDATOR_GAV = "com.okworx.ilcd.validation:ilcd-validation:3.0.0";
  private static final String PROFILE_GAV = "com.okworx.ilcd.validation.profiles:EPD-1.2-OEKOBAUDAT:3.8.0";

  private IlcdProfileValidator() {}

  public static void main(String[] args) {
    int exit = 3;
    Path output = null;
    try {
      var parsed = Args.parse(args);
      output = parsed.output;
      var receipt = validate(parsed);
      writeJson(output, receipt);
      int errors = ((Number) receipt.get("error_count")).intValue();
      if (errors > 0) {
        System.err.println("RESULT: TECHNICAL_ILCD_EPD_PROFILE_ERRORS");
        System.err.println("Validation errors: " + errors);
        exit = 2;
      } else {
        System.out.println("RESULT: TECHNICAL_ILCD_EPD_PROFILE_ZERO_ERRORS");
        System.out.println("ERROR events: 0");
        exit = 0;
      }
    } catch (Exception ex) {
      try {
        if (output != null) {
          var failure = new TreeMap<String, Object>();
          failure.put("verdict", "VALIDATOR_RUNTIME_FAILURE");
          failure.put("certified", false);
          failure.put("engine", Map.of("name", ENGINE, "version", ENGINE_VERSION));
          failure.put("failure_type", ex.getClass().getName());
          failure.put("message", String.valueOf(ex.getMessage()));
          failure.put("timestamp_utc", Instant.now().toString());
          failure.put("limitations", limitations());
          writeJson(output, failure);
        }
      } catch (Exception ignored) {
        // Preserve the original failure as the process result.
      }
      ex.printStackTrace(System.err);
      exit = 3;
    }
    System.exit(exit);
  }

  private static Map<String, Object> validate(Args args) throws Exception {
    requireFile(args.profileJar, "profile JAR");
    requireFile(args.validatorJar, "validator JAR");
    if (!Files.exists(args.input)) {
      throw new IllegalArgumentException("input path not found: " + args.input);
    }

    URL profileUrl = args.profileJar.toUri().toURL();
    Profile profile = ProfileManager.getInstance().registerProfile(profileUrl);
    if (profile == null) {
      throw new IllegalStateException("profile registration returned null");
    }

    var chain = new ValidatorChain();
    chain.add(new SchemaValidator());
    chain.add(new XSLTStylesheetValidator());
    chain.setProfile(profile);
    chain.setReportSuccesses(true);

    var builder = new ReferenceBuilder();
    builder.build(args.input.toFile());
    HashMap<String, IDatasetReference> references = new HashMap<>(builder.getReferences());
    if (references.isEmpty()) {
      throw new IllegalStateException("ReferenceBuilder found no ILCD dataset references under: " + args.input);
    }
    chain.setObjectsToValidate(references);
    chain.validate();

    var events = new ArrayList<Map<String, Object>>();
    int errorCount = 0;
    int warningCount = 0;
    int successCount = 0;
    int otherCount = 0;

    for (IValidationEvent event : chain.getEventsList().getEvents()) {
      if (event == null) {
        continue;
      }
      String severity = event.getSeverity() == null ? "UNDEFINED" : event.getSeverity().name();
      switch (severity) {
        case "ERROR" -> errorCount++;
        case "WARNING" -> warningCount++;
        case "SUCCESS" -> successCount++;
        default -> otherCount++;
      }
      var item = new TreeMap<String, Object>();
      item.put("severity", severity);
      item.put("message", String.valueOf(event.getMessage()));
      IDatasetReference ref = event.getReference();
      if (ref == null) {
        item.put("reference", null);
      } else {
        var refMap = new TreeMap<String, Object>();
        refMap.put("dataset_type", ref.getDatasetType() == null ? null : ref.getDatasetType().name());
        refMap.put("uuid", ref.getUuid());
        refMap.put("version", ref.getVersion());
        refMap.put("uri", ref.getUri());
        refMap.put("name", ref.getName());
        item.put("reference", refMap);
      }
      events.add(item);
    }

    events.sort(Comparator.comparing(IlcdProfileValidator::eventSortKey));

    var referenceReceipt = new ArrayList<Map<String, Object>>();
    references.values().stream()
        .sorted(Comparator.comparing(IlcdProfileValidator::referenceSortKey))
        .forEach(ref -> {
          var item = new TreeMap<String, Object>();
          item.put("dataset_type", ref.getDatasetType() == null ? null : ref.getDatasetType().name());
          item.put("uuid", ref.getUuid());
          item.put("version", ref.getVersion());
          item.put("uri", ref.getUri());
          item.put("name", ref.getName());
          referenceReceipt.add(item);
        });

    var profileMetadata = profileMetadata(args.profileJar, profile);
    var fixture = fixtureReceipt(args.input);
    var dependencies = new TreeMap<String, Object>();
    dependencies.put("validator", Map.of(
        "gav", VALIDATOR_GAV,
        "jar", args.validatorJar.getFileName().toString(),
        "sha256", sha256(args.validatorJar)));
    dependencies.put("profile", Map.of(
        "gav", PROFILE_GAV,
        "jar", args.profileJar.getFileName().toString(),
        "sha256", sha256(args.profileJar),
        "metadata", profileMetadata));

    String eventDigest = sha256(canonicalBytes(events));
    var receipt = new TreeMap<String, Object>();
    receipt.put("verdict", errorCount == 0
        ? "TECHNICAL_ILCD_EPD_PROFILE_ZERO_ERRORS"
        : "TECHNICAL_ILCD_EPD_PROFILE_ERRORS");
    receipt.put("certified", false);
    receipt.put("engine", Map.of("name", ENGINE, "version", ENGINE_VERSION));
    receipt.put("runtime", Map.of(
        "java_version", System.getProperty("java.version"),
        "java_vendor", System.getProperty("java.vendor"),
        "os_name", System.getProperty("os.name"),
        "os_arch", System.getProperty("os.arch")));
    receipt.put("dependencies", dependencies);
    receipt.put("fixture", fixture);
    receipt.put("dataset_references", referenceReceipt);
    receipt.put("event_count", events.size());
    receipt.put("error_count", errorCount);
    receipt.put("warning_count", warningCount);
    receipt.put("success_count", successCount);
    receipt.put("other_count", otherCount);
    receipt.put("events_sha256", eventDigest);
    receipt.put("events", events);
    receipt.put("limitations", limitations());
    receipt.put("technical_conformance_claimed", false);
    receipt.put("timestamp_utc", Instant.now().toString());

    var digestPayload = new TreeMap<>(receipt);
    digestPayload.remove("timestamp_utc");
    receipt.put("deterministic_receipt_sha256", sha256(canonicalBytes(digestPayload)));
    return receipt;
  }

  private static List<String> limitations() {
    return List.of(
        "This harness records technical ILCD/profile validation only; it does not establish scientific validity, product representativeness, programme-operator verification, professional review, regulatory approval, or certification.",
        "A zero-error result is not permitted to become a ProofGrid technical-conformance claim until the fixture provenance/license and positive acceptance criteria in issue #12 are satisfied.",
        "Validator/profile dependencies are third-party open-source artifacts resolved at runtime and are not RegenExcalibur-owned datasets.");
  }

  private static Map<String, Object> profileMetadata(Path profileJar, Profile profile) throws IOException {
    var result = new TreeMap<String, Object>();
    result.put("profile_name", profile.getName());
    result.put("profile_version", profile.getVersion());
    try (JarFile jar = new JarFile(profileJar.toFile())) {
      var manifest = jar.getManifest();
      if (manifest != null) {
        Attributes attrs = manifest.getAttributes("ILCD-Validator-Profile");
        if (attrs != null) {
          result.put("manifest_profile_name", attrs.getValue("Profile-Name"));
          result.put("manifest_profile_version", attrs.getValue("Profile-Version"));
        }
        result.put("implementation_title", manifest.getMainAttributes().getValue("Implementation-Title"));
        result.put("implementation_version", manifest.getMainAttributes().getValue("Implementation-Version"));
      }
    }
    return result;
  }

  private static Map<String, Object> fixtureReceipt(Path input) throws Exception {
    var files = new ArrayList<Map<String, Object>>();
    if (Files.isRegularFile(input)) {
      files.add(fileEntry(input.getParent(), input));
    } else {
      try (var stream = Files.walk(input)) {
        stream.filter(Files::isRegularFile)
            .sorted(Comparator.comparing(path -> input.relativize(path).toString()))
            .forEach(path -> {
              try {
                files.add(fileEntry(input, path));
              } catch (Exception ex) {
                throw new RuntimeException(ex);
              }
            });
      }
    }
    var receipt = new TreeMap<String, Object>();
    receipt.put("root", input.toString());
    receipt.put("files", files);
    receipt.put("tree_sha256", sha256(canonicalBytes(files)));
    return receipt;
  }

  private static Map<String, Object> fileEntry(Path root, Path file) throws Exception {
    var result = new TreeMap<String, Object>();
    result.put("path", root.relativize(file).toString().replace(File.separatorChar, '/'));
    result.put("size", Files.size(file));
    result.put("sha256", sha256(file));
    return result;
  }

  private static String eventSortKey(Map<String, Object> event) {
    return String.valueOf(event.get("severity")) + "|"
        + String.valueOf(event.get("reference")) + "|"
        + String.valueOf(event.get("message"));
  }

  private static String referenceSortKey(IDatasetReference ref) {
    return String.valueOf(ref.getDatasetType()) + "|"
        + String.valueOf(ref.getUuid()) + "|"
        + String.valueOf(ref.getVersion()) + "|"
        + String.valueOf(ref.getUri());
  }

  private static ObjectMapper mapper() {
    var mapper = new ObjectMapper();
    mapper.configure(MapperFeature.SORT_PROPERTIES_ALPHABETICALLY, true);
    mapper.configure(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS, true);
    return mapper;
  }

  private static byte[] canonicalBytes(Object value) throws Exception {
    return mapper().writeValueAsBytes(value);
  }

  private static void writeJson(Path path, Object value) throws Exception {
    Files.createDirectories(path.toAbsolutePath().getParent());
    String json = mapper().writerWithDefaultPrettyPrinter().writeValueAsString(value) + "\n";
    Files.writeString(path, json, StandardCharsets.UTF_8);
  }

  private static String sha256(Path path) throws Exception {
    return sha256(Files.readAllBytes(path));
  }

  private static String sha256(byte[] value) throws Exception {
    MessageDigest digest = MessageDigest.getInstance("SHA-256");
    byte[] hash = digest.digest(value);
    StringBuilder out = new StringBuilder(hash.length * 2);
    for (byte b : hash) {
      out.append(String.format("%02x", b));
    }
    return out.toString();
  }

  private static void requireFile(Path path, String label) {
    if (!Files.isRegularFile(path)) {
      throw new IllegalArgumentException(label + " not found: " + path);
    }
  }

  private static final class Args {
    final Path input;
    final Path output;
    final Path profileJar;
    final Path validatorJar;

    private Args(Path input, Path output, Path profileJar, Path validatorJar) {
      this.input = input;
      this.output = output;
      this.profileJar = profileJar;
      this.validatorJar = validatorJar;
    }

    static Args parse(String[] args) {
      Map<String, String> values = new HashMap<>();
      for (int i = 0; i < args.length; i += 2) {
        if (i + 1 >= args.length || !args[i].startsWith("--")) {
          throw new IllegalArgumentException(
              "usage: --input <path> --output <json> --profile-jar <jar> --validator-jar <jar>");
        }
        values.put(args[i], args[i + 1]);
      }
      for (String key : List.of("--input", "--output", "--profile-jar", "--validator-jar")) {
        if (!values.containsKey(key)) {
          throw new IllegalArgumentException("missing required argument " + key);
        }
      }
      return new Args(
          Path.of(values.get("--input")),
          Path.of(values.get("--output")),
          Path.of(values.get("--profile-jar")),
          Path.of(values.get("--validator-jar")));
    }
  }
}
