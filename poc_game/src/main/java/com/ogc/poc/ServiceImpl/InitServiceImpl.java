package com.ogc.poc.ServiceImpl;

import java.util.ArrayList;
import java.util.List;
import java.util.ResourceBundle;

import org.slf4j.Logger;
import org.springframework.stereotype.Service;

import com.ogc.poc.Service.InitService;
import com.ogc.poc.model.AwardsInfo;
import com.ogc.poc.model.InitGameResponse;
import com.ogc.poc.model.Payline;
import com.ogc.poc.model.PaylineInfo;
import com.ogc.poc.model.Paylines;
import com.ogc.poc.model.Reel;
import com.ogc.poc.model.ReelInfo;
import com.ogc.poc.model.ReelSet;

@Service
public class InitServiceImpl implements InitService {

	Logger logger = org.slf4j.LoggerFactory.getLogger(getClass());

	@Override
	public InitGameResponse getInitResponse() {
		InitGameResponse gameResponse = new InitGameResponse();
		gameResponse.setType("Init");
/*		payLine  payLine= new PayLine();*/
		List<Reel> reelList = new ArrayList<Reel>();
		ResourceBundle reelset = ResourceBundle.getBundle("ruleBook");
		String s = null;
		for (int i = 1; i <= Integer.parseInt(reelset.getString("reelNumber")); i++) {
			String reelSet1 = reelset.getString("reelSet" + i);
			Reel reel = new Reel(reelSet1);
			reel.setReelIndex(String.valueOf(i));
			reel.setLength("23");
			System.out.println(reelSet1);
			reel.setValue(reelSet1);
			reelList.add(reel);
			System.out.println(reelList);
		}
		List<ReelSet> reelSetList = new ArrayList<>();
		ReelSet reelSet = new ReelSet();
		reelSet.setReel(reelList);
		reelSetList.add(reelSet);
		ReelInfo reelInfo = new ReelInfo();
		reelInfo.setReelSet(reelSetList);
		System.out.println(reelInfo);
		gameResponse.setReelInfo(reelInfo);
		
		
		
		Paylines payLines = new Paylines();
		PaylineInfo payLineInfo= new PaylineInfo();
/*		AwardsInfo awardInfo = new  AwardsInfo();*/
		List<Payline> payLineList=new ArrayList<>();
		for (int i = 1; i <= Integer.parseInt(reelset.getString("paylineCount")); i++) {
			String payLine1 = reelset.getString("payLine" + i);
			Payline payLine= new Payline();
			payLine.setValue(payLine1);
			payLine.setIndex(String.valueOf(i));
			payLine.setSelectable("N");
			payLineList.add(payLine);
			System.out.println(payLineList);
		}
		payLineInfo.setPayLine(payLineList);
		payLineInfo.setDefault1(Integer.parseInt(reelset.getString("paylineCount"))-1);
		payLineInfo.setPaylineCount(reelset.getString("paylineCount"));
		payLines.setPaylineInfo(payLineInfo);
		payLines.setGameMode("0");
		gameResponse.setPayLines(payLines);
		return gameResponse;
	}

}
