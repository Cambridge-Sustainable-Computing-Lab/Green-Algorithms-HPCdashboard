# Grafana Tips

To change the datasource of an existing dashboard.
Laurent: Two ways


1  - via the web interface (but then I think you need to edit each chart of the dashboard with the new datasource)

2  -  In the JSON file by replacing the first bit of the file
```
  "__inputs": [
    {
      "name": "DS_GRAFANA-POSTGRESQL-GA_DB", <= Optional change, just in case you want to change the variable name
      "label": "grafana-postgresql-ga_db",   <= Grafana name of the datasource to change
      "description": "",
      "type": "datasource",
      "pluginId": "grafana-postgresql-datasource", <= Change if the database engine is different
      "pluginName": "PostgreSQL".                  <= Change if the database engine is different
    }
  ],
```  
If you want to change the variable name, then you will need to change each variable occurence in the JSON file.
e.g., in rows like this:
```
"uid": "${DS_GRAFANA-POSTGRESQL-GA_DB}"
```

Laurent managed to save the JSON with a second existing datasource (just editing 1 chart). He saved it by switching on the Export dashboard to use in another instance:

![Image showing how to export a dashboard](exporting_dashboard.png?raw=true "Exporting dashboard")

Then the JSON looks like this:

```
{
  "__inputs": [
    {
      "name": "DS_GRAFANA-POSTGRESQL-NEW-GA",
      "label": "grafana-postgresql-new-ga",
      "description": "",
      "type": "datasource",
      "pluginId": "grafana-postgresql-datasource",
      "pluginName": "PostgreSQL"
    },
    {
      "name": "DS_GRAFANA-POSTGRESQL-GA_DB",
      "label": "grafana-postgresql-ga_db",
      "description": "",
      "type": "datasource",
      "pluginId": "grafana-postgresql-datasource",
      "pluginName": "PostgreSQL"
    }
  ],

  ...
  ...
  datasource": {
        "type": "grafana-postgresql-datasource",
        "uid": "${DS_GRAFANA-POSTGRESQL-NEW-GA}"
  },
  ...
  ...
  datasource": {
        "type": "grafana-postgresql-datasource",
        "uid": "${DS_GRAFANA-POSTGRESQL-NEW-GA}"
  },
  ...
  ```

  [Back to Contents](./Contents.md)