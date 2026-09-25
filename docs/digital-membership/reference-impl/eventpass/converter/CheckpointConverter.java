package com.airtel.userprofile.eventpass.converter;

import com.airtel.userprofile.eventpass.enums.Checkpoint;
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

/** Lets {@code @RequestParam Checkpoint} bind from a string, mirroring ContestEntryTypeConverter. */
@Component
public class CheckpointConverter implements Converter<String, Checkpoint> {

	@Override
	public Checkpoint convert(String source) {
		return Checkpoint.fromValue(source);
	}
}
