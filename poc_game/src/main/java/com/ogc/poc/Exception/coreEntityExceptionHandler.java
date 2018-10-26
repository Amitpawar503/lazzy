package com.ogc.poc.Exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import com.ogc.poc.Exception.ApiiError;

@ControllerAdvice
public class coreEntityExceptionHandler {

	@ExceptionHandler(CoreException.class)
	public ResponseEntity<ApiiError> exceptionHandler(CoreException ex) {
		ApiiError error = new ApiiError(ex.getErrCode(),HttpStatus.BAD_REQUEST, ex.getErrMsg());
		return new ResponseEntity<ApiiError>(error, HttpStatus.BAD_REQUEST);

	}

}
