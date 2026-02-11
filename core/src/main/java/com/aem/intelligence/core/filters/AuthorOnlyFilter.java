package com.aem.intelligence.core.filters;

import org.apache.jackrabbit.api.security.user.Authorizable;
import org.apache.jackrabbit.api.security.user.Group;
import org.apache.jackrabbit.api.security.user.User;
import org.apache.jackrabbit.api.security.user.UserManager;
import com.aem.intelligence.core.conf.AIConfiguration;
import org.apache.sling.api.SlingHttpServletRequest;
import org.apache.sling.api.SlingHttpServletResponse;
import org.apache.sling.servlets.annotations.SlingServletFilter;
import org.apache.sling.servlets.annotations.SlingServletFilterScope;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.metatype.annotations.Designate;
import org.osgi.framework.Constants;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.*;
import java.io.IOException;
import java.util.Iterator;

/**
 * Filter to ensure only users in the 'authors' group can access the Ollama API.
 */
@Component(
    service = Filter.class,
    property = {
        Constants.SERVICE_DESCRIPTION + "=AEM Intelligence Engine - Author Security Filter",
        Constants.SERVICE_RANKING + ":Integer=100"
    }
)
@SlingServletFilter(
    scope = {SlingServletFilterScope.REQUEST},
    pattern = "/bin/ollama/.*",
    methods = {"GET", "POST"}
)
@Designate(ocd = AIConfiguration.class)
public class AuthorOnlyFilter implements Filter {

    private static final Logger LOG = LoggerFactory.getLogger(AuthorOnlyFilter.class);
    private AIConfiguration config;

    @Activate
    protected void activate(AIConfiguration config) {
        this.config = config;
    }

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        // No initialization required
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        
        if (!(request instanceof SlingHttpServletRequest) || !(response instanceof SlingHttpServletResponse)) {
            chain.doFilter(request, response);
            return;
        }

        SlingHttpServletResponse slingResponse = (SlingHttpServletResponse) response;

        // 1. Check if Engine is enabled
        if (config != null && !config.enabled()) {
            slingResponse.sendError(SlingHttpServletResponse.SC_FORBIDDEN, "AEM Intelligence Engine is disabled.");
            return;
        }

        SlingHttpServletRequest slingRequest = (SlingHttpServletRequest) request;

        try {
            UserManager userManager = slingRequest.getResourceResolver().adaptTo(UserManager.class);
            if (userManager == null) {
                LOG.error("UserManager is null");
                slingResponse.sendError(SlingHttpServletResponse.SC_INTERNAL_SERVER_ERROR, "UserManager not available");
                return;
            }

            Authorizable currentUser = userManager.getAuthorizable(slingRequest.getUserPrincipal());
            if (currentUser == null || !(currentUser instanceof User)) {
                slingResponse.sendError(SlingHttpServletResponse.SC_FORBIDDEN, "User not authenticated");
                return;
            }

            if (isAllowed(currentUser)) {
                chain.doFilter(request, response);
            } else {
                slingResponse.sendError(SlingHttpServletResponse.SC_FORBIDDEN, "Access denied: User is not authorized to use AEM Intelligence.");
            }

        } catch (Exception e) {
            LOG.error("Error in AEM Intelligence security filter", e);
            slingResponse.sendError(SlingHttpServletResponse.SC_INTERNAL_SERVER_ERROR, "Security check failed: " + e.getMessage());
        }
    }

    private boolean isAllowed(Authorizable user) {
        try {
            // Default allowed groups if config is missing (safety net)
            String[] allowedGroups = (config != null) ? config.allowedGroups() : new String[]{"authors", "administrators"};
            
            Iterator<Group> groups = user.memberOf();
            while (groups.hasNext()) {
                Group group = groups.next();
                String groupId = group.getID();
                for (String allowedGroup : allowedGroups) {
                     if (allowedGroup.equals(groupId)) {
                         return true;
                     }
                }
            }
        } catch (Exception e) {
            LOG.error("Error checking user group membership", e);
        }
        return false;
    }

    @Override
    public void destroy() {
        // Cleanup if needed
    }
}
