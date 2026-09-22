import React from "react";

export default function Filters({ filters, setFilters, facets, hasResume }) {
  const up = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });

  return (
    <aside className="filters">
      <div className="filter-group">
        <label>Search title / company</label>
        <input value={filters.q} onChange={up("q")} placeholder="e.g. Backend Engineer" />
      </div>

      <div className="filter-group">
        <label>Category</label>
        <select value={filters.category} onChange={up("category")}>
          <option value="">All categories</option>
          {(facets.categories || []).map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Country</label>
        <select value={filters.country} onChange={up("country")}>
          <option value="">All countries</option>
          {(facets.countries || []).map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Minimum salary</label>
        <input
          type="number"
          value={filters.min_salary}
          onChange={up("min_salary")}
          placeholder="e.g. 2000000"
        />
      </div>

      <div className="filter-group">
        <label>Posted since</label>
        <input type="date" value={filters.date_from} onChange={up("date_from")} />
      </div>

      {hasResume && (
        <div className="filter-group">
          <label>Sort by</label>
          <select value={filters.sort} onChange={up("sort")}>
            <option value="recent">Most recent</option>
            <option value="match">Best resume match</option>
          </select>
        </div>
      )}

      <button
        className="btn btn-ghost full"
        onClick={() =>
          setFilters({ ...filters, q: "", category: "", country: "", min_salary: "", date_from: "" })
        }
      >
        Clear filters
      </button>
    </aside>
  );
}
