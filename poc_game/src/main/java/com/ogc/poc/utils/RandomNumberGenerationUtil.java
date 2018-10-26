package com.ogc.poc.utils;

import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;


public abstract class RandomNumberGenerationUtil {

	public static int getRandomNumberInRange(int min, int max) {

		if (min >= max) {
			throw new IllegalArgumentException("max must be greater than min");
		}

		Random r = new Random();
		return r.nextInt((max - min) + 1) + min;
	}

	public static int getRandomNumberByThreadLocal(int min, int max) {
		return ThreadLocalRandom.current().nextInt(min, max);
	}
}