package com.airtel.userprofile.eventpass.service.impl;

import com.airtel.userprofile.eventpass.config.QrStyleProperties;
import com.airtel.userprofile.eventpass.dto.request.QrRenderRequest;
import com.airtel.userprofile.eventpass.dto.response.QrRenderResponse;
import com.airtel.userprofile.eventpass.service.QrImageService;
import com.airtel.userprofile.eventpass.util.CircularQrGenerator;
import com.airtel.userprofile.eventpass.util.CircularQrGenerator.Style;
import com.airtel.userprofile.eventpass.util.HexColors;
import com.airtel.userprofile.eventpass.util.QrImageDecoder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * Adapts the web layer to the render utils: resolves the configured {@link QrStyleProperties} into a
 * {@link Style}, layers the request's non-null overrides on top, and delegates to {@link
 * CircularQrGenerator}/{@link QrImageDecoder}.
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
		return QrRenderResponse.builder()
				.imageDataUri(generator.renderDataUri(request.getData(), style))
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

	/** Config defaults, with the request's non-null fields overriding them ("" centreText hides text). */
	private Style resolve(QrRenderRequest req) {
		Style.StyleBuilder b = Style.from(props).toBuilder();
		if (req.getCenterText() != null) b.centerText(req.getCenterText());
		if (StringUtils.hasText(req.getGradientInnerColor())) b.gradientInner(HexColors.parse(req.getGradientInnerColor()));
		if (StringUtils.hasText(req.getGradientOuterColor())) b.gradientOuter(HexColors.parse(req.getGradientOuterColor()));
		if (StringUtils.hasText(req.getFinderColor())) b.finderColor(HexColors.parse(req.getFinderColor()));
		if (req.getBackgroundColor() != null) b.background(HexColors.parse(req.getBackgroundColor()));
		if (req.getSize() != null && req.getSize() > 0) b.size(req.getSize());
		return b.build();
	}
}
