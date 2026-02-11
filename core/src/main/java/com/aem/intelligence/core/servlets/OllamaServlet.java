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
    "sling.servlet.methods=POST"
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

    @Activate
    protected void activate(Config config) {
        this.ollamaUrl = config.ollama_url();
        this.modelName = config.model_name();
        this.pythonGatewayUrl = config.python_gateway_url();
        LOG.info("OllamaServlet activated. URL: {}, Model: {}, Gateway: {}", ollamaUrl, modelName, pythonGatewayUrl);
    }

    @Override
    protected void doPost(SlingHttpServletRequest request, SlingHttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        String prompt = request.getParameter("prompt");
        if (prompt == null || prompt.trim().isEmpty()) {
            response.setStatus(400);
            response.getWriter().write("{\"error\": \"Prompt parameter is required\"}");
            return;
        }

        long startTime = System.currentTimeMillis();

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
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(contextPayload.toString(), StandardCharsets.UTF_8))
                        .build();

                HttpResponse<String> contextResponse = client.send(contextRequest, HttpResponse.BodyHandlers.ofString());
                long pythonDuration = System.currentTimeMillis() - pythonStart;
                LOG.info("Python Context call took {} ms", pythonDuration);
                
                if (contextResponse.statusCode() == 200) {
                     // Simple JSON parsing using Gson (compatible with older versions)
                     JsonObject responseJson = new com.google.gson.JsonParser().parse(contextResponse.body()).getAsJsonObject();
                     if (responseJson.has("context")) {
                         retrievedContext = responseJson.get("context").getAsString();
                     }
                } else {
                    LOG.warn("Python Gateway returned error: {}", contextResponse.statusCode());
                }
            } catch (Exception e) {
                LOG.error("Failed to fetch context from Python layer", e);
                // Continue without context
            }

            // 2. Construct RAG Prompt
            String systemPrompt;
            if (retrievedContext != null && !retrievedContext.isEmpty()) {
                systemPrompt = String.format(
                    "You are an AEM Expert. Use the following context from the WKND site to answer the question concisely. If the answer isn't in the context, say you don't know.%n%n Context: %s %n%n Question: %s", 
                    retrievedContext, prompt
                );
            } else {
                systemPrompt = prompt; // Fallback to raw prompt
            }

            // 3. Call Ollama
            long ollamaStart = System.currentTimeMillis();
            JsonObject requestPayload = new JsonObject();
            requestPayload.addProperty("model", this.modelName);
            requestPayload.addProperty("prompt", systemPrompt);
            requestPayload.addProperty("stream", false);

            HttpRequest httpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(this.ollamaUrl))
                    .timeout(Duration.ofMinutes(5))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(requestPayload.toString(), StandardCharsets.UTF_8))
                    .build();

            HttpResponse<String> httpResponse = client.send(httpRequest, HttpResponse.BodyHandlers.ofString());
            long ollamaDuration = System.currentTimeMillis() - ollamaStart;
            LOG.info("Ollama call took {} ms. Total duration: {} ms", ollamaDuration, (System.currentTimeMillis() - startTime));

            if (httpResponse.statusCode() == 200) {
                response.getWriter().write(httpResponse.body());
            } else {
                LOG.error("Ollama API failed with status: {}", httpResponse.statusCode());
                response.setStatus(502);
                response.getWriter().write("{\"error\": \"Ollama API failed\"}");
            }

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            LOG.error("Interrupted while calling Ollama", e);
            response.setStatus(500);
            response.getWriter().write("{\"error\": \"Internal Server Error\"}");
        } catch (Exception e) {
            LOG.error("Error calling Ollama", e);
            response.setStatus(500);
            response.getWriter().write("{\"error\": \"Internal Server Error\"}");
        }
    }
}
