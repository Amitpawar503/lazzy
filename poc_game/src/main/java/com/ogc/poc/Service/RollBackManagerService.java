package com.ogc.poc.Service;

import java.io.IOException;
import java.net.MalformedURLException;

import javax.xml.bind.JAXBException;

import com.ogc.poc.Exception.ApiiError;
import com.ogc.poc.Exception.CoreException;
import com.ogc.poc.model.RollbackResponse;
import com.ogc.poc.model.Player;
import com.ogc.poc.model.RollBack;


public interface RollBackManagerService {

	public RollbackResponse doroll(String request,String sessionId) throws CoreException,MalformedURLException,IOException,JAXBException;
}
