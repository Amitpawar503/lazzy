package com.ogc.poc.model;
/*package com.ogc.poc.model.beans;

import java.util.HashMap;
import java.util.List;

import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlRootElement;

@XmlRootElement(name = "AwardInfo")
public class AwardInfo {
	@XmlAttribute
	private Integer awardTableIndex;
	@XmlAttribute
	private Double awardCount;
	@XmlAttribute
	private Double maxWin;

}
*/

public class AwardsInfo
{
    private String awardTableIndex;

    private String awardCount;

    private String maxWin;

    private Award[] Award;

    public String getAwardTableIndex ()
    {
        return awardTableIndex;
    }

    public void setAwardTableIndex (String awardTableIndex)
    {
        this.awardTableIndex = awardTableIndex;
    }

    public String getAwardCount ()
    {
        return awardCount;
    }

    public void setAwardCount (String awardCount)
    {
        this.awardCount = awardCount;
    }

    public String getMaxWin ()
    {
        return maxWin;
    }

    public void setMaxWin (String maxWin)
    {
        this.maxWin = maxWin;
    }

    public Award[] getAward ()
    {
        return Award;
    }

    public void setAward (Award[] Award)
    {
        this.Award = Award;
    }

    @Override
    public String toString()
    {
        return "ClassPojo [awardTableIndex = "+awardTableIndex+", awardCount = "+awardCount+", maxWin = "+maxWin+", Award = "+Award+"]";
    }
}
			
		