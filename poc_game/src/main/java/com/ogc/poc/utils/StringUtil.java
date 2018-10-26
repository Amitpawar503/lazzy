package com.ogc.poc.utils;

import org.apache.commons.lang3.StringUtils;

public abstract class StringUtil extends StringUtils {

	public static String ifEmptyThenNotAvilable(String string) {
		if (isBlank(string))
			return "NA";
		else
			return string;

	}
}