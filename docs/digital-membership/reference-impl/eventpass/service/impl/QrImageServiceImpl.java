package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.config.QrStyleProperties;
import com.airtel.userprofile.eventpass.dto.request.QrRenderRequest;
import com.airtel.userprofile.eventpass.dto.response.QrRenderResponse;
import com.airtel.userprofile.eventpass.service.QrImageService;
import com.airtel.userprofile.eventpass.util.CircularQrGenerator;
import com.airtel.userprofile.eventpass.util.CircularQrGenerator.Style;
import com.airtel.userprofile.eventpass.util.QrImageDecoder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * Ties the configured {@link QrStyleProperties} to the {@link CircularQrGenerator}/{@link
 * QrImageDecoder} utils, applying any per-request overrides on top of the config defaults.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class QrImageServiceImpl implements QrImageService {

	private final QrStyleProperties props;
	private final CircularQrGenerator generator;
	private final QrImageDecoder decoder;

	@Override
	public QrRenderResponse render(QrRenderRequest request) {
		Style style = resolve(request);
		byte[] png = generator.renderPng(request.getData(), style);
		String dataUri = "data:image/png;base64," + java.util.Base64.getEncoder().encodeToString(png);
		return QrRenderResponse.builder()
				.imageDataUri(dataUri)
				.width(style.getSize())
				.height(style.getSize())
				.encoded(request.getData())
				.build();
	}

	@Override
	public byte[] renderPng(String data) {
		return generator.renderPng(data, Style.from(props));
	}

	@Override
	public String decode(byte[] imageBytes) {
		return decoder.decode(imageBytes);
	}

	/** Config defaults, with non-null request fields overriding them. */
	private Style resolve(QrRenderRequest req) {
		Style.StyleBuilder b = Style.from(props).toBuilder();
		if (req.getCenterText() != null) b.centerText(req.getCenterText()); // "" hides text
		if (StringUtils.hasText(req.getGradientInnerColor())) b.gradientInner(CircularQrGenerator.parseColor(req.getGradientInnerColor()));
		if (StringUtils.hasText(req.getGradientOuterColor())) b.gradientOuter(CircularQrGenerator.parseColor(req.getGradientOuterColor()));
		if (StringUtils.hasText(req.getFinderColor())) b.finderColor(CircularQrGenerator.parseColor(req.getFinderColor()));
		if (req.getBackgroundColor() != null) b.background(CircularQrGenerator.parseColor(req.getBackgroundColor()));
		if (req.getSize() != null && req.getSize() > 0) b.size(req.getSize());
		return b.build();
	}
}
