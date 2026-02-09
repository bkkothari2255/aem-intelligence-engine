package com.aem.intelligence.core.listeners;

import org.apache.sling.api.resource.ResourceResolverFactory;
import org.apache.sling.api.resource.observation.ResourceChange;
import org.apache.sling.api.resource.observation.ResourceChangeListener;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.ConfigurationPolicy;
import org.osgi.service.component.annotations.Reference;
import org.osgi.service.metatype.annotations.AttributeDefinition;
import org.osgi.service.metatype.annotations.Designate;
import org.osgi.service.metatype.annotations.ObjectClassDefinition;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Component(
    service = ResourceChangeListener.class,
    immediate = true,
    property = {
        ResourceChangeListener.PATHS + "=/content",
        ResourceChangeListener.CHANGES + "=ADDED",
        ResourceChangeListener.CHANGES + "=CHANGED",
        ResourceChangeListener.CHANGES + "=REMOVED"
    },
    configurationPolicy = ConfigurationPolicy.REQUIRE
)
@Designate(ocd = ContentChangeListener.Config.class)
public class ContentChangeListener implements ResourceChangeListener {

    private static final Logger LOG = LoggerFactory.getLogger(ContentChangeListener.class);
    private static final Set<String> VALID_EXTENSIONS = Set.of("html", "json");

    @ObjectClassDefinition(name = "AEM Intelligence - Content Listener", description = "Listens for content changes and sends them to the enrichment engine.")
    public @interface Config {
        @AttributeDefinition(name = "Enabled", description = "Enable or disable the listener.")
        boolean enabled() default true;

        @AttributeDefinition(name = "Enrichment Endpoint", description = "URL of the enrichment engine.")
        String endpointUrl() default "http://localhost:8000/enrich";
    }

    private boolean enabled;
    private String endpointUrl;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    @Activate
    protected void activate(Config config) {
        this.enabled = config.enabled();
        this.endpointUrl = config.endpointUrl();
        LOG.info("ContentChangeListener activated. Enabled: {}, Endpoint: {}", enabled, endpointUrl);
    }

    @Override
    public void onChange(List<ResourceChange> changes) {
        if (!enabled) {
            return;
        }

        for (ResourceChange change : changes) {
            String path = change.getPath();
            if (isValidPath(path)) {
                LOG.debug("Detected change at: {}", path);
                executor.submit(() -> sendToEnrichment(path, change.getType()));
            }
        }
    }

    private boolean isValidPath(String path) {
        return path.startsWith("/content") && !path.contains("/jcr:system") && !path.contains("/rep:policy");
    }

    private void sendToEnrichment(String path, ResourceChange.ChangeType type) {
        try {
            URL url = new URL(endpointUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);

            String jsonInputString = String.format("{\"path\": \"%s\", \"type\": \"%s\"}", path, type.name());

            try (var os = conn.getOutputStream()) {
                byte[] input = jsonInputString.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }

            int responseCode = conn.getResponseCode();
            LOG.info("Sent update for {} to enrichment engine. Response: {}", path, responseCode);
            conn.disconnect();

        } catch (IOException e) {
            LOG.error("Failed to send update to enrichment engine", e);
        }
    }
}
