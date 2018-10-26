package com.ogc.poc.ServiceImpl;

import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.List;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Marshaller;
import javax.xml.bind.Unmarshaller;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.ogc.poc.Controller.RollBackController;
import com.ogc.poc.Exception.ApiiError;
import com.ogc.poc.Exception.CoreException;
import com.ogc.poc.Helper.RollBackHelper;
import com.ogc.poc.Repo.RollBackRepository;
import com.ogc.poc.Service.RollBackManagerService;
import com.ogc.poc.model.RollbackResponse;
import com.ogc.poc.model.Player;
import com.ogc.poc.model.RollBack;

import org.eclipse.persistence.jaxb.MarshallerProperties;
import org.eclipse.persistence.jaxb.UnmarshallerProperties;

@Service
public class RollBackManagerServiceImpl implements RollBackManagerService {

	private static final Logger LOGGER = LogManager.getLogger(RollBackManagerServiceImpl.class);

	@Autowired
	public RollBackHelper rollHelper;

	@Autowired
	public RollBackRepository repo;

	public Player roll;

	@Override
	public RollbackResponse doroll(String request, String sessionId) throws CoreException, IOException, JAXBException {
		// TODO Auto-generated method stub
		RollbackResponse response=null;
		LOGGER.info("RollBackManagerServiceImpl :: doroll Enter");
		if (rollHelper.rollValidate(request, sessionId))
			try {
				{
					
					RestTemplate restTemplate=new RestTemplate();
					String fooResourceUrl
					  = "http://localhost:8082/wiapi/mockapi?request=rollback&loginname=nogsuser&password=qwerty&apiversion=1.5&gamesessionid=ccbcecef-1c04-42db-b90e-6e880d64e68c&accountid=sgi_camp1&nogsgameid=456&rollbackamount=12.5&roundid=1&transactionid=12345&product=casino&gametype=slots&gamemodel=5reels&gpid=102&currency=INR&device=desktop";
					
					 response = restTemplate.getForObject(fooResourceUrl, RollbackResponse.class);
					 
					 LOGGER.info("RollBack Response value:{}",response.toString());
					 LOGGER.info("RollBack Response value:{}",restTemplate.getForObject(fooResourceUrl, Object.class));
				}

			} catch (

			Exception e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		else {
			LOGGER.error("RollBackManagerServiceImpl :: doroll Error");
			throw new CoreException("E117", "Invalid Request parameter");
		}
		LOGGER.info("RollBackManagerServiceImpl :: doroll Exit");
		return response;
	}

}
