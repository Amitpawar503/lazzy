package com.ogc.poc.coremodule;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;

@SpringBootApplication(scanBasePackages = {"com.ogc.poc"})
@EnableMongoRepositories("com.ogc.poc")
public class CoreModuleApplication{
	
	public static void main(String[] args) {
		SpringApplication.run(CoreModuleApplication.class, args);
	}
}
