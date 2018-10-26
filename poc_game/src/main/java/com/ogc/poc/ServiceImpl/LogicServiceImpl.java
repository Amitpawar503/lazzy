package com.ogc.poc.ServiceImpl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.ResourceBundle;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.ogc.poc.Exception.CoreException;
import com.ogc.poc.Helper.LogicHelper;
import com.ogc.poc.Service.LogicService;
import com.ogc.poc.model.GameResult;
import static com.ogc.poc.utils.RandomNumberGenerationUtil.getRandomNumberByThreadLocal;
import static com.ogc.poc.Constants.RollBackConstants.BASE_GAME;
import static com.ogc.poc.Constants.RollBackConstants.FREE_GAME;
import static com.ogc.poc.Constants.RollBackConstants.YES;
import static com.ogc.poc.Constants.RollBackConstants.WILD;
import static com.ogc.poc.Constants.RollBackConstants.FREE_SPIN;

import static org.apache.commons.lang3.StringUtils.isNotBlank;

@Service
public class LogicServiceImpl implements LogicService {

	private static final Logger LOGGER = LogManager.getLogger(LogicServiceImpl.class);
	private static ResourceBundle rbb = ResourceBundle.getBundle("ruleBook");
	private static ResourceBundle rff = ResourceBundle.getBundle("FruleBook");
	private static boolean isFree = false;
	public static int freeGame = 0;
	public HashMap<String, List<String>> reelSet = new HashMap<>();

	@Autowired
	public LogicHelper logicHelper;

	private HashMap<String, List<String>> loadReelSet(String gameType, ResourceBundle common) throws CoreException {

		LOGGER.info("LogicServiceImpl:ENTER:loadReelSet");

		for (int i = 1; i <= Integer.parseInt(realData("reelNumber", common)); i++) {
			List<String> reelValue = Stream.of(common.getString("reelSet" + i).split(",")).map(item -> item)
					.collect(Collectors.toList());
			reelSet.put("reelSet" + i, reelValue);
		}

		LOGGER.info("LogicServiceImpl:loadReelSet: VALUE:{}", reelSet.entrySet());
		LOGGER.info("LogicServiceImpl:EXIT:loadReelSet");

		return reelSet;
	}

	public List<GameResult> getLogic(String gametype, String autoPlay) throws CoreException {

		List<GameResult> game = new ArrayList<>();
		if (isNotBlank(autoPlay) && Integer.parseInt(autoPlay) > 0) {
			for (int i = 0; i < Integer.parseInt(autoPlay); i++) {
				game.add(gamelogic(BASE_GAME));
			}
		} else
			game.add(gamelogic(BASE_GAME));
		return game;
	}

	public GameResult gamelogic(String gameType) throws CoreException {

		LOGGER.info("LogicServiceImpl:ENTER:getLogic");

		ResourceBundle common = null;
		if (FREE_GAME.equals(gameType)) {
			if (isFree) {
				common = rff;
				freeGame = 0;
			} else {
				throw new CoreException("E116", "Invalid Request: You Don't have Free Spin");
			}
		} else if (BASE_GAME.equals(gameType)) {
			common = rbb;
		}

		int total = 0;
		int payLineCount = 0;
		int jackpotWin = 0;

		loadReelSet(gameType, common);
		Map<String, List<String>> reelValue = getVisibleWindow(gameType, common);
		LOGGER.info("LogicServiceImpl::getLogic:compare:{}", reelValue.toString());

		String[] aww = common.getString("id").split(",");
		String wildValue = common.getString(WILD);
		String freeSpinValue = common.getString(FREE_SPIN);
		List<String> offSet = reelValue.get("reelValue");

		List<Integer> payline = new ArrayList<Integer>();
		for (int i = 1; i <= Integer.parseInt(realData("payLineNumber", common)); i++) {

			LOGGER.info("LogicServiceImpl::getLogic:payline" + i);
			String[] pos = common.getString("payLine" + i).split(",");
			int payLineSize = pos.length;
			for (String award : aww) {
				int count = 0;
				int jackpot = 0;

				for (String check : pos) {
					int payLineValue = Integer.parseInt(check);
					if (offSet.get(payLineValue).equals(award) || offSet.get(payLineValue).equals(wildValue)) {
						count++;
						if (offSet.get(payLineValue).equals(wildValue)) {
							jackpot++;
						}
					} else if (!offSet.get(payLineValue).equals(award)) {
						break;
					}
					if (offSet.get(payLineValue).equals(freeSpinValue)) {
						freeGame++;
						LOGGER.info("LogicServiceImpl::getLogic:COUNT FREE SPIN:{}", freeGame);
					}

				}
				LOGGER.info("LogicServiceImpl::getLogic:COUNT:{}", count);
				if (payLineSize == jackpot) {
					jackpotWin = jackpotWin + 3500;
					break;
				} else if (payLineSize == count) {
					total = total + logicHelper.giveWinAmount(award);
					payline.add(i);
				}
			}
		}

		GameResult game = new GameResult();

		checkFreeSpin(gameType, reelValue, game, common);
		game.setTotalWin(String.valueOf(total));
		game.setPayLineCount(String.valueOf(payline.size()));
		game.setPayLine(payline);
		game.setJackpotAmount(String.valueOf(jackpotWin));
		game.setType(gameType);
		game.setReelStop(reelValue.get("randomValue"));
		LOGGER.info("LogicServiceImpl:EXIT:getLogic");
		return game;
	}

	private Map<String, List<String>> getVisibleWindow(String gameType, ResourceBundle common) {

		Map<String, List<String>> offSet = new HashMap<>();
		offSet.put("randomValue", new ArrayList<>());
		offSet.put("reelValue", new ArrayList<>());

		int reelCount = Integer.parseInt(realData("reelNumber", common));
		for (int i = 1; i <= reelCount; i++) {
			int rand = getRandomNumberByThreadLocal(0, 30);
			offSet.get("randomValue").add(String.valueOf(rand));
			for (int j = 0; j < 3; j++) {
				if (rand <= 29)
					offSet.get("reelValue").add(reelSet.get("reelSet" + i).get(rand + j));
				else
					offSet.get("reelValue").add(reelSet.get("reelSet" + i).get(rand));
			}
			LOGGER.info("LogicServiceImpl::getLogic:rand_count:{}", rand);
		}
		return offSet;
	}

	/**
	 * This method will Check for Free Spin
	 * 
	 * @param gameType
	 * @param reelValue
	 * @param game
	 */
	private void checkFreeSpin(String gameType, Map<String, List<String>> reelValue, GameResult game,
			ResourceBundle common) {
		LOGGER.info("LogicServiceImpl::isFree", isFree);
		if (gameType.equalsIgnoreCase(BASE_GAME) && isFreeSpin(reelValue, common)) {
			game.setFreeSpin(YES);
			isFree = true;
		}
	}

	private boolean isFreeSpin(Map<String, List<String>> reelValue, ResourceBundle common) {
		int freeSpinCount = 0;
		int reelNumber = Integer.parseInt(realData("reelNumber", common));
		LOGGER.info("LogicServiceImpl::isFreeSpin:isFree", isFree);
		for (int i = 0; i < reelNumber * reelNumber; i++) {
			if (reelValue.get("reelValue").get(i).equals(realData(FREE_SPIN, common)))
				freeSpinCount++;
		}
		return freeSpinCount > 2;
	}

	private static String realData(String realParam, ResourceBundle common) {
		return common.getString(realParam);
	}

}
