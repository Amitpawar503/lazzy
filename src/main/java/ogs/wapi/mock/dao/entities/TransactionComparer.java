package ogs.wapi.mock.dao.entities;

import java.util.function.Predicate;

public class TransactionComparer<T> implements Predicate<T>
{

	public T trans1;
	@Override
	public boolean test(T trans2) 
	{
		if(((GameTransaction)trans1).getTransactionId()== ((GameTransaction)trans2).getTransactionId())
		{
			return true;
		}
		else
		{
			return false;
		}
	}
	  
}
