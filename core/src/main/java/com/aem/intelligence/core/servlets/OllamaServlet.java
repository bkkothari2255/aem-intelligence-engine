package com.aem.intelligence.core.servlets;

import com.google.gson.JsonObject;

import org.apache.sling.api.SlingHttpServletRequest;
import org.apache.sling.api.SlingHttpServletResponse;
import org.apache.sling.api.servlets.SlingAllMethodsServlet;
import org.osgi.service.component.annotations.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.Servlet;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;

import org.osgi.service.component.annotations.Activate;
import org.osgi.service.metatype.annotations.AttributeDefinition;
import org.osgi.service.metatype.annotations.Designate;
import org.osgi.service.metatype.annotations.ObjectClassDefinition;

@Component(service = Servlet.class, property = {
    "sling.servlet.paths=/bin/ollama/generate",
    "sling.servlet.methods={POST, GET}"
})
@Designate(ocd = OllamaServlet.Config.class)
public class OllamaServlet extends SlingAllMethodsServlet {

    @ObjectClassDefinition(name = "AEM Intelligence - Ollama Servlet", description = "Configuration for Ollama Bridge")
    public @interface Config {
        @AttributeDefinition(name = "Ollama API URL", description = "URL of the Ollama generation endpoint")
        String ollama_url() default "http://localhost:11434/api/generate";
        
        @AttributeDefinition(name = "Model Name", description = "Default model to use")
        String model_name() default "llama3.1";

        @AttributeDefinition(name = "Python Gateway URL", description = "URL of the Python Intelligence Layer")
        String python_gateway_url() default "http://localhost:8000/api/v1/context";
    }

    private static final Logger LOG = LoggerFactory.getLogger(OllamaServlet.class);
    private String ollamaUrl;
    private String modelName;
    private String pythonGatewayUrl;
    
    private static final HttpClient client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    private static final String APPLICATION_JSON = "application/json";

    @Activate
    protected void activate(Config config) {
        this.ollamaUrl = config.ollama_url();
        this.modelName = config.model_name();
        this.pythonGatewayUrl = config.python_gateway_url();
        LOG.info("OllamaServlet activated. URL: {}, Model: {}, Gateway: {}", ollamaUrl, modelName, pythonGatewayUrl);
    }

    @Override
    protected void doGet(SlingHttpServletRequest request, SlingHttpServletResponse response) throws IOException {
        response.setContentType(APPLICATION_JSON);
        response.setCharacterEncoding("UTF-8");

        // Refined approach:
        // Python: http://localhost:8000/docs or just / (FastAPI usually has docs)
        // Ollama: http://localhost:11434/ (Ollama returns "Ollama is running")

        String ollamaBaseUrl = this.ollamaUrl.replace("/api/generate", "");
        String pythonBaseUrl = this.pythonGatewayUrl.replace("/api/v1/context", "");

        boolean ollamaUp = checkUrl(ollamaBaseUrl);
        boolean pythonUp = checkUrl(pythonBaseUrl);

        JsonObject json = new JsonObject();
        json.addProperty("python", pythonUp);
        json.addProperty("ollama", ollamaUp);
        
        response.getWriter().write(json.toString());
    }

    private boolean checkUrl(String url) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(2))
                    .GET()
                    .build();
            HttpResponse<Void> response = client.send(request, HttpResponse.BodyHandlers.discarding());
            return response.statusCode() >= 200 && response.statusCode() < 500; 
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        } catch (Exception e) {
            return false;
        }
    }

    @Override
    protected void doPost(SlingHttpServletRequest request, SlingHttpServletResponse response) throws IOException {
        response.setContentType(APPLICATION_JSON);
        response.setCharacterEncoding("UTF-8");

        String prompt = request.getParameter("prompt");
        if (prompt == null || prompt.trim().isEmpty()) {
            response.setStatus(400);
            response.getWriter().write("{\"error\": \"Prompt parameter is required\"}");
            return;
        }

        try {
            // 1. Fetch Context from Python Intelligence Layer
            String retrievedContext = "";
            try {
                long pythonStart = System.currentTimeMillis();
                JsonObject contextPayload = new JsonObject();
                contextPayload.addProperty("query", prompt);

                HttpRequest contextRequest = HttpRequest.newBuilder()
                        .uri(URI.create(this.pythonGatewayUrl))
                        .timeout(Duration.ofSeconds(30))
                        .header("Content-Type", APPLICATION_JSON)
                        .POST(HttpRequest.BodyPublishers.ofString(contextPayload.toString(), StandardCharsets.UTF_8))
                        .build();

                HttpResponse<String> contextResponse = client.send(contextRequest, HttpResponse.BodyHandlers.ofString());
                long pythonDuration = System.currentTimeMillis() - pythonStart;
                LOG.info("Python Context call took {} ms", pythonDuration);
                
                if (contextResponse.statusCode() == 200) {
                     JsonObject responseJson = new com.google.gson.JsonParser().parse(contextResponse.body()).getAsJsonObject();
                     if (responseJson.has("context")) {
                         retrievedContext = responseJson.get("context").getAsString();
                     }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw e; // Re-throw to be caught by outer block or handled
            } catch (Exception e) {
                LOG.error("Failed to fetch context from Python layer", e);
            }

            // 2. Construct RAG Prompt
            String systemPrompt;
            if (retrievedContext != null && !retrievedContext.isEmpty()) {
                systemPrompt = String.format(
                    "You are an AEM Expert. Use the following context from the WKND site to answer the question concisely. If the answer isn't in the context, say you don't know.%%n%%n Context: %s %%n%%n Question: %s", 
                    retrievedContext, prompt
                );
            } else {
                systemPrompt = prompt;
            }

            // 3. Call Ollama with Streaming
            JsonObject requestPayload = new JsonObject();
            requestPayload.addProperty("model", this.modelName);
            requestPayload.addProperty("prompt", systemPrompt);
            requestPayload.addProperty("stream", true); // Enable streaming

            HttpRequest httpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(this.ollamaUrl))
                    .timeout(Duration.ofMinutes(5))
                    .header("Content-Type", APPLICATION_JSON)
                    .POST(HttpRequest.BodyPublishers.ofString(requestPayload.toString(), StandardCharsets.UTF_8))
                    .build();

            // Set response type for streaming (NDJSON)
            response.setContentType("application/x-ndjson");
            
            HttpResponse<java.io.InputStream> httpResponse = client.send(httpRequest, HttpResponse.BodyHandlers.ofInputStream());

            if (httpResponse.statusCode() == 200) {
                try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.InputStreamReader(httpResponse.body(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        response.getWriter().write(line + "\n");
                        response.getWriter().flush(); // Send chunk to client
                    }
                }
                LOG.info("Streaming complete for prompt: {}", prompt);
            } else {
                LOG.error("Ollama API failed with status: {}", httpResponse.statusCode());
                response.setStatus(502);
                response.getWriter().write("{\"error\": \"Ollama API failed\"}");
            }

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            LOG.error("Interrupted while calling Ollama", e);
        } catch (Exception e) {
            LOG.error("Error calling Ollama", e);
            response.setStatus(500);
            response.getWriter().write("{\"error\": \"Internal Server Error\"}");
        }
    }
}
