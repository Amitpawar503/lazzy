package com.airtel.userprofile.eventpass.controller;

import com.airtel.core.dto.genericResponse.Response;
import com.airtel.core.enums.Entity;
import com.airtel.core.enums.Operation;
import com.airtel.core.logging.AuditLog;
import com.airtel.userprofile.eventpass.dto.request.QrRenderRequest;
import com.airtel.userprofile.eventpass.dto.response.QrRenderResponse;
import com.airtel.userprofile.eventpass.service.QrImageService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;

/**
 * Utility surface for the styled circular QR — render any payload into the Advantage-Club image, and
 * read one back. Colours/centre text come from {@code eventpass.qr-style.*} config, with per-request
 * overrides on the render body.
 *
 * <p>Generation of the <em>member's</em> signed QR string stays on {@link MembershipQrController}
 * (API 4). This controller turns any payload — that token, or a deeplink / info — into the picture,
 * and validates a scanned/uploaded picture back to its payload.
 */
@RestController
@Api(value = "Event Pass — QR image util (render & validate)")
@Slf4j
@RequiredArgsConstructor
public class MembershipQrImageController {

	private final QrImageService qrImageService;

	/** Render a styled QR (PNG data URI) for the given payload + optional colour/centre-text overrides. */
	@PostMapping("/v1/membership/qr/image")
	@ApiOperation(value = "Render a styled circular QR (data URI) for any token/deeplink/info")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<QrRenderResponse> render(@Valid @RequestBody QrRenderRequest request) {
		return Response.getSuccessResponse(qrImageService.render(request));
	}

	/** Same render, but stream the PNG directly (e.g. for an {@code <img src>} URL). */
	@PostMapping(value = "/v1/membership/qr/image.png", produces = MediaType.IMAGE_PNG_VALUE)
	@ApiOperation(value = "Render a styled circular QR as raw PNG bytes")
	public byte[] renderPng(@Valid @RequestBody QrRenderRequest request) {
		return qrImageService.renderPng(request.getData());
	}

	/**
	 * Validate/read a scanned or uploaded QR image back to its payload (structural check). Trust
	 * validation of the recovered token is the entry path's job ({@code QrTokenService.verify}).
	 */
	@PostMapping(value = "/v1/membership/qr/validate-image", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
	@ApiOperation(value = "Decode a QR image and return the payload it carries")
	@AuditLog(entity = Entity.USERPROFILE, operation = Operation.API, createNewLog = true, publishEvent = false)
	public Response<Map<String, String>> validateImage(@RequestParam("image") MultipartFile image) throws IOException {
		String payload = qrImageService.decode(image.getBytes());
		return Response.getSuccessResponse(Map.of("data", payload));
	}
}
