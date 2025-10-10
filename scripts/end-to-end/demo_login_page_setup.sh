g_dir=/usr/share/grafana/public/build/
app_title='GA Dashboard - Demo'

# Change title
find $g_dir -name *.js \
    -exec sed -i "s|LoginTitle=\"Welcome to Grafana\"|LoginTitle=\"${app_title}\"|g" {} \; \
    -exec sed -i "s|AppTitle=\"Grafana\"|AppTitle=\"${app_title}\"|g" {} \; \

# Email or username
find $g_dir -name *.js \
    -exec sed -i 's|Email or username"|Email or username (e.g. uid_1)"|g' {} \; \
    -exec sed -i 's|Password"|Password (e.g. user1)"|g' {} \; \