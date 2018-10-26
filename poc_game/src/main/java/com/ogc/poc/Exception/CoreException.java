package com.ogc.poc.Exception;

public class CoreException extends Exception {
	private String errMsg;
	
	private String errCode;

	public String getErrCode() {
		return errCode;
	}

	public void setErrCode(String errCode) {
		this.errCode = errCode;
	}

	public String getErrMsg() {
		return errMsg;
	}

	public void setErrMsg(String errMsg) {
		this.errMsg = errMsg;
	}

	public CoreException(String code,String msg) {
		this.errMsg=msg;
		this.errCode=code;
	}

}
