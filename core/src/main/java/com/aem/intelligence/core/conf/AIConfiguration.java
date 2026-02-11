package com.aem.intelligence.core.conf;

import org.osgi.service.metatype.annotations.AttributeDefinition;
import org.osgi.service.metatype.annotations.AttributeType;
import org.osgi.service.metatype.annotations.ObjectClassDefinition;

@ObjectClassDefinition(name = "AEM Intelligence - Engine Configuration", description = "Configuration for the AI Intelligence Engine")
public @interface AIConfiguration {

    @AttributeDefinition(
        name = "Enable Intelligence Engine",
        description = "If disabled, all AI requests will be blocked.",
        type = AttributeType.BOOLEAN
    )
    boolean enabled() default true;

    @AttributeDefinition(
        name = "Allowed Groups",
        description = "User groups allowed to access the AI Engine. Default is 'authors' and 'administrators'.",
        type = AttributeType.STRING
    ) // Using String array in implementation, but simple string here for default simple config or array
    String[] allowedGroups() default {"authors", "administrators"};
}
