package ogs.wapi.mock.controllers;

import ogs.wapi.mock.dto.RSP;
import ogs.wapi.mock.services.OGSException;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

@ControllerAdvice
@RestController
public class OGSErrorController extends ResponseEntityExceptionHandler
{
	  @ExceptionHandler(OGSException.class)
	  public final ResponseEntity<RSP> handleOGSException(OGSException ex, WebRequest request) {
	    RSP errorDetails = new RSP();
	    errorDetails.apiVersion = "1.5";
	    errorDetails.msg = ex.getMsg();
	    errorDetails.rc = ex.getRc();
	    errorDetails.request = ex.getRequest();
	    return new ResponseEntity<>(errorDetails, HttpStatus.OK);
	  }
}
