/*
 * OtterTune - PostgresCollector.java
 *
 * Copyright (c) 2017-18, Carnegie Mellon University Database Group
 */

package com.controller.collectors;

import com.controller.util.FileUtil;
import com.controller.util.JSONUtil;
import com.controller.util.json.JSONException;
import com.controller.util.json.JSONObject;
import com.controller.util.json.JSONStringer;
import org.apache.log4j.Logger;

import java.sql.*;
import java.util.*;

public class PostgresCollector extends DBCollector {
  private static final String NEXT_CONF_PATH="/ottertune/client/driver/next_config.json";
//private static final String NEXT_CONF_PATH="E:/Workspace/Workspace_Java/ottertune/client/driver/next_config.json";
  private static final String QEMU_PARAMETER="qemu_parameter";
  private static final String CPU_NUMBER="cpu_number";
  private static final String QEMU_NUMBER="qemu_number";
  private static final String MEMORY_SIZE="memory_size";
  private static final String HARDWARE_QUEUE_NUMBER="hardware_queue_number";


  private static final Logger LOG = Logger.getLogger(PostgresCollector.class);

  private static final String VERSION_SQL = "SELECT version();";

  private static final String PARAMETERS_SQL = "SHOW ALL;";

  private boolean oldVersion = false;

  private static final String[] PG_STAT_VIEWS = {
    "pg_stat_archiver", "pg_stat_bgwriter", "pg_stat_database",
    "pg_stat_database_conflicts", "pg_stat_user_tables", "pg_statio_user_tables",
    "pg_stat_user_indexes", "pg_statio_user_indexes"
  };

  private static final String[] PG_STAT_VIEWS_OLD_VERSION = {
    "pg_stat_bgwriter", "pg_stat_database",
    "pg_stat_database_conflicts", "pg_stat_user_tables", "pg_statio_user_tables",
    "pg_stat_user_indexes", "pg_statio_user_indexes"
  };

  private static final String[] PG_STAT_VIEWS_LOCAL_DATABASE = {
    "pg_stat_database", "pg_stat_database_conflicts"
  };
  private static final String PG_STAT_VIEWS_LOCAL_DATABASE_KEY = "datname";
  private static final String[] PG_STAT_VIEWS_LOCAL_TABLE = {
    "pg_stat_user_tables", "pg_statio_user_tables"
  };
  private static final String PG_STAT_VIEWS_LOCAL_TABLE_KEY = "relname";
  private static final String[] PG_STAT_VIEWS_LOCAL_INDEXES = {
    "pg_stat_user_indexes", "pg_statio_user_indexes"
  };
  private static final String PG_STAT_VIEWS_LOCAL_INDEXES_KEY = "relname";

  private final Map<String, List<Map<String, String>>> pgMetrics;

  public PostgresCollector(String oriDBUrl, String username, String password) {
    pgMetrics = new HashMap<>();
    try {
      Connection conn = DriverManager.getConnection(oriDBUrl, username, password);

      Statement s = conn.createStatement();

      // Collect DBMS version
      ResultSet out = s.executeQuery(VERSION_SQL);
      if (out.next()) {
        String[] outStr = out.getString(1).split(" ");
        String[] verStr = outStr[1].split("\\.");
        this.version.append(verStr[0]);
        this.version.append(".");
        this.version.append(verStr[1]);
      }

      // Collect DBMS parameters
      out = s.executeQuery(PARAMETERS_SQL);
      while (out.next()) {
        dbParameters.put(out.getString("name"), out.getString("setting"));
      }

      // Collect DBMS internal metrics
      String[] pgStatViews = PG_STAT_VIEWS;
      if (Float.parseFloat(this.version.toString()) < 9.4) {
        this.oldVersion = true;
        pgStatViews = PG_STAT_VIEWS_OLD_VERSION;
      }

      for (String viewName : pgStatViews) {
        out = s.executeQuery("SELECT * FROM " + viewName);
        pgMetrics.put(viewName, getMetrics(out));
      }
      conn.close();
    } catch (SQLException e) {
      e.printStackTrace();
      LOG.error("Error while collecting DB parameters: " + e.getMessage());
    }
  }

  @Override
  public boolean hasMetrics() {
    return (pgMetrics.isEmpty() == false);
  }
// generate json object map
  private JSONObject genMapJSONObj(Map<String, String> mapin) {
    JSONObject res = new JSONObject();
    try {
      for (String key : mapin.keySet()) {
        res.put(key, mapin.get(key));
      }
    } catch (JSONException je) {
      LOG.error(je);
    }
    return res;
  }
// generate local json object
  private JSONObject genLocalJSONObj(String viewName, String jsonKeyName) {
    JSONObject thisViewObj = new JSONObject();
    List<Map<String, String>> thisViewList = pgMetrics.get(viewName);
    try {
      for (Map<String, String> dbmap : thisViewList) {
        String jsonkey = dbmap.get(jsonKeyName);
        thisViewObj.put(jsonkey, genMapJSONObj(dbmap));
      }
    } catch (JSONException je) {
      LOG.error(je);
    }
    return thisViewObj;
  }

  @Override
  public String collectMetrics() {
    JSONStringer stringer = new JSONStringer();
    try {
      stringer.object();
      stringer.key(JSON_GLOBAL_KEY);
      // create global objects for two views: "pg_stat_archiver" and "pg_stat_bgwriter"
      JSONObject jobGlobal = new JSONObject();
      // "pg_stat_archiver" (only one instance in the list) >= version 9.4
      if (!this.oldVersion) {
        Map<String, String> archiverList = pgMetrics.get("pg_stat_archiver").get(0);
        jobGlobal.put("pg_stat_archiver", genMapJSONObj(archiverList));
      }

      // "pg_stat_bgwriter" (only one instance in the list)
      Map<String, String> bgwriterList = pgMetrics.get("pg_stat_bgwriter").get(0);
      jobGlobal.put("pg_stat_bgwriter", genMapJSONObj(bgwriterList));

      // add global json object
      stringer.value(jobGlobal);
      stringer.key(JSON_LOCAL_KEY);
      // create local objects for the rest of the views
      JSONObject jobLocal = new JSONObject();

      // "table"
      JSONObject jobTable = new JSONObject();
      for (int i = 0; i < PG_STAT_VIEWS_LOCAL_TABLE.length; i++) {
        String viewName = PG_STAT_VIEWS_LOCAL_TABLE[i];
        String jsonKeyName = PG_STAT_VIEWS_LOCAL_TABLE_KEY;
        jobTable.put(viewName, genLocalJSONObj(viewName, jsonKeyName));
      }
      jobLocal.put("table", jobTable);

      // "database"
      JSONObject jobDatabase = new JSONObject();
      for (int i = 0; i < PG_STAT_VIEWS_LOCAL_DATABASE.length; i++) {
        String viewName = PG_STAT_VIEWS_LOCAL_DATABASE[i];
        String jsonKeyName = PG_STAT_VIEWS_LOCAL_DATABASE_KEY;
        jobDatabase.put(viewName, genLocalJSONObj(viewName, jsonKeyName));
      }
      jobLocal.put("database", jobDatabase);

      // "indexes"
      JSONObject jobIndexes = new JSONObject();
      for (int i = 0; i < PG_STAT_VIEWS_LOCAL_INDEXES.length; i++) {
        String viewName = PG_STAT_VIEWS_LOCAL_INDEXES[i];
        String jsonKeyName = PG_STAT_VIEWS_LOCAL_INDEXES_KEY;
        jobIndexes.put(viewName, genLocalJSONObj(viewName, jsonKeyName));
      }
      jobLocal.put("indexes", jobIndexes);

      // add local json object
      stringer.value(jobLocal);
      stringer.endObject();

    } catch (JSONException jsonexn) {
      jsonexn.printStackTrace();
    }

    return JSONUtil.format(stringer.toString());
  }
// get metrics List<Map>
  private static List<Map<String, String>> getMetrics(ResultSet out) throws SQLException {
    ResultSetMetaData metadata = out.getMetaData();
    int numColumns = metadata.getColumnCount();
    String[] columnNames = new String[numColumns];
    for (int i = 0; i < numColumns; ++i) {
      columnNames[i] = metadata.getColumnName(i + 1).toLowerCase();
    }
    
    List<Map<String, String>> metrics = new ArrayList<Map<String, String>>();
    while (out.next()) {
      Map<String, String> metricMap = new TreeMap<String, String>();
      for (int i = 0; i < numColumns; ++i) {
        metricMap.put(columnNames[i], out.getString(i + 1));
      }
      metrics.add(metricMap);
    }
    return metrics;
  }

  @Override
  public String collectParameters() {
    JSONStringer stringer = new JSONStringer();
    try {
      stringer.object();
      stringer.key(JSON_GLOBAL_KEY);
      JSONObject jobLocal = new JSONObject();
      JSONObject job = new JSONObject();
//      add qemu hardware first
      org.json.JSONObject jsonObjectRaw= FileUtil.getJsonObject(NEXT_CONF_PATH);
      org.json.JSONObject jsonObject=jsonObjectRaw.getJSONObject(QEMU_PARAMETER);
      LOG.info("Main.collectParameters jsonObject="+jsonObject);
      System.out.println("Main.collectParameters jsonObject="+jsonObject);
      System.out.println("Main.collectParameters jsonObject.keySize="+jsonObject.keySet().size());
      //job.put(CPU_NUMBER,jsonObject.getInt(CPU_NUMBER));
      //job.put(QEMU_NUMBER,jsonObject.getInt(QEMU_NUMBER));
      //job.put(MEMORY_SIZE,jsonObject.getString(MEMORY_SIZE));
      //job.put(HARDWARE_QUEUE_NUMBER,jsonObject.getInt(HARDWARE_QUEUE_NUMBER));

      for (String k : dbParameters.keySet()) {
        job.put(k, dbParameters.get(k));
      }
      // "global is a fake view_name (a placeholder)"
      LOG.info("PostgresCollector.collectParameter() Parameter Information="+job.toString());
      jobLocal.put("global", job);
      stringer.value(jobLocal);
      stringer.key(JSON_LOCAL_KEY);
      stringer.value(null);
      stringer.endObject();
    } catch (JSONException jsonexn) {
      jsonexn.printStackTrace();
    }
    return JSONUtil.format(stringer.toString());
  }

  public static void main(String[] args) {
    PostgresCollector postgresCollector =new PostgresCollector("jdbc:postgresql://10.0.2.41:5432/tpcc",
            "postgres","test123");
    LOG.info(postgresCollector.collectParameters());
    System.out.println(postgresCollector.collectParameters());

  }
}
