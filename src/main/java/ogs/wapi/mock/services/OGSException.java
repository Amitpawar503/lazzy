package ogs.wapi.mock.services;


public class OGSException extends RuntimeException
{
	private String request;
	
	private Integer rc;

	private String msg;

	public String getRequest() {
		return request;
	}

	public void setRequest(String request) {
		this.request = request;
	}



	public String getMsg() {
		return msg;
	}

	public void setMsg(String msg) {
		this.msg = msg;
	}

	public Integer getRc() {
		return rc;
	}

	public void setRc(Integer rc) {
		this.rc = rc;
	}
}
