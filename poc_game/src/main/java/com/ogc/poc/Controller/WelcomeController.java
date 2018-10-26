package com.ogc.poc.Controller;

import java.util.ResourceBundle;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import com.ogc.poc.Repo.RollBackRepository;
import com.ogc.poc.model.Welcome;



@Controller
public class WelcomeController {
	private static final String welcomemsg = "Welcome %s!";

	@Autowired
	public RollBackRepository repository;
	
	
	@GetMapping("/welcome/user")
	@ResponseBody
	public Welcome welcomeUser(@RequestParam(name = "name", required = false, defaultValue = "health check working") String name) {
		
		repository.findRollBackData(name);
		System.out.println(repository.count());
		return new Welcome(String.format(welcomemsg, name));
		
	}
	
	@GetMapping("/welcome")
	@ResponseBody
	public Welcome welcomeUser2(@RequestParam(name = "name", required = false, defaultValue = "health check working") String name) {
		
		
		return new Welcome(String.format(welcomemsg, name));
		
	}

}
