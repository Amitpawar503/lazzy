package ogs.wapi.mock.services;

import java.io.Serializable;

import ogs.wapi.mock.services.exception.GenericServiceException;

import org.springframework.data.repository.CrudRepository;

public interface GenericService <T, ID extends Serializable>
{
	public default Iterable<T> findAll() {
		return getRepository().findAll();
	}
	
	public default T get(ID id) {
		return getRepository().findOne(id);
	}
	
	public default T save(T entity) {
		return getRepository().save(entity);
	}
	
	public default void delete(ID id) {
		if (getRepository().exists(id)) {
			getRepository().delete(id);
		}
		else {
			throw new GenericServiceException(">> 'id' doesn't exists: " + id);
		}
	}
	
	public default void update(T entity) {
		if (getRepository().exists(getId(entity))) {
			getRepository().save(entity);
		}
		else {
			throw new GenericServiceException("Can't update Rating because it doesn't exist in DB: " + entity);
		}
	}
	
	public ID getId(T entity);
	
	public CrudRepository<T, ID> getRepository();
}
