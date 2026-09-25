package com.airtel.userprofile.eventpass.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

/**
 * Environment-tunable knobs (no redeploy needed). The QR TTL is shared by generation (API 4) and
 * validation (API 3) — issuance and validation MUST read the same value (Q1; recommend 5 min).
 */
@Data
@Component
@RefreshScope
@ConfigurationProperties(prefix = "eventpass")
public class EventPassProperties {

	/** QR token TTL in seconds (Q1 — recommend 300). */
	private long qrTtlSeconds = 300;

	/** Agent scanning session TTL in seconds (24h). */
	private long agentSessionTtlSeconds = 86_400;

	/** Token schema version currently issued; verifier accepts this and older supported versions. */
	private int tokenVersion = 1;

	/** JWT issuer claim. */
	private String issuer = "airtel-userprofile-eventpass";

	/** Active signing key id (KMS/HSM alias) for rotation. */
	private String signingKeyId;
}
