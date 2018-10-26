package com.ogc.poc.model;

import java.util.List;

import com.fasterxml.jackson.dataformat.xml.annotation.JacksonXmlRootElement;

@JacksonXmlRootElement(localName = "GameResponse")
public class GameResult extends GameResponse {

	public String stake;
	public String stakePerLine;
	public String payLineCount;
	public String totalWin;
	public String freeSpin = "N";
	public List<String> reelStop;
	public List<Integer> payLine;
	public String jackpotAmount;

	public String getJackpotAmount() {
		return jackpotAmount;
	}

	public void setJackpotAmount(String jackpotAmount) {
		this.jackpotAmount = jackpotAmount;
	}

	public List<Integer> getPayLine() {
		return payLine;
	}

	public void setPayLine(List<Integer> payline2) {
		this.payLine = payline2;
	}

	public List<String> getReelStop() {
		return reelStop;
	}

	public void setReelStop(List<String> reelStop) {
		this.reelStop = reelStop;
	}

	public String getFreeSpin() {
		return freeSpin;
	}

	public void setFreeSpin(String freeSpin) {
		this.freeSpin = freeSpin;
	}

	public String getStake() {
		return stake;
	}

	public void setStake(String stake) {
		this.stake = stake;
	}

	public String getStakePerLine() {
		return stakePerLine;
	}

	public void setStakePerLine(String stakePerLine) {
		this.stakePerLine = stakePerLine;
	}

	public String getPayLineCount() {
		return payLineCount;
	}

	public void setPayLineCount(String payLineCount) {
		this.payLineCount = payLineCount;
	}

	public String getTotalWin() {
		return totalWin;
	}

	public void setTotalWin(String totalWin) {
		this.totalWin = totalWin;
	}

	@Override
	public String toString() {
		return "GameResult [stake=" + stake + ", stakePerLine=" + stakePerLine + ", payLineCount=" + payLineCount
				+ ", totalWin=" + totalWin + ", freeSpin=" + freeSpin + ", reelStop=" + reelStop + ", payLine="
				+ payLine + ", jackpotAmount=" + jackpotAmount + "]";
	}

}
