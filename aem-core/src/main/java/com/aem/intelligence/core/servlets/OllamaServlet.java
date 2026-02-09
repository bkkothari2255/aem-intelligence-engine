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

@Component(service = Servlet.class, property = {
    "sling.servlet.paths=/bin/ollama/generate",
    "sling.servlet.methods=POST"
})
public class OllamaServlet extends SlingAllMethodsServlet {

    private static final Logger LOG = LoggerFactory.getLogger(OllamaServlet.class);
    private static final String OLLAMA_API_URL = "http://localhost:11434/api/generate";
    private static final HttpClient client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(10))
            .build();

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

        try {
            JsonObject requestPayload = new JsonObject();
            requestPayload.addProperty("model", "llama3.1");
            requestPayload.addProperty("prompt", prompt);
            requestPayload.addProperty("stream", false);

            HttpRequest httpRequest = HttpRequest.newBuilder()
                    .uri(URI.create(OLLAMA_API_URL))
                    .timeout(Duration.ofMinutes(2)) // LLMs can be slow
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(requestPayload.toString(), StandardCharsets.UTF_8))
                    .build();

            HttpResponse<String> httpResponse = client.send(httpRequest, HttpResponse.BodyHandlers.ofString());

            if (httpResponse.statusCode() == 200) {
                // Return the raw response from Ollama
                response.getWriter().write(httpResponse.body());
            } else {
                LOG.error("Ollama API failed with status params: {}", httpResponse.statusCode());
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
