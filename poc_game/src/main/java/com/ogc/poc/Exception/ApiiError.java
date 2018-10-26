package com.ogc.poc.Exception;

import org.springframework.http.HttpStatus;

public class ApiiError{

	private HttpStatus status;
	private String errMsg;
	private String errCode;

	public String getErrCode() {
		return errCode;
	}

	public void setErrCode(String errCode) {
		this.errCode = errCode;
	}

	public ApiiError(String code,HttpStatus status, String errMsg) {
		super();
		this.status = status;
		this.errMsg = errMsg;
		this.errCode=code;
	}

	public HttpStatus getStatus() {
		return status;
	}

	public void setStatus(HttpStatus status) {
		this.status = status;
	}

	public String getErrMsg() {
		return errMsg;
	}

	public void setErrMsg(String errMsg) {
		this.errMsg = errMsg;
	}

}
