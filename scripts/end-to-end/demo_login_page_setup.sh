g_dir=/usr/share/grafana/public/build/
app_title='Green Algorithms Dashboard [demo]'

# Change title
find $g_dir -name *.js \
    -exec sed -i "s|LoginTitle=\"Welcome to Grafana\"|LoginTitle=\"${app_title}\"|g" {} \; \
    -exec sed -i "s|AppTitle=\"Grafana\"|AppTitle=\"${app_title}\"|g" {} \; \

# Add subtitle
subtitle2replace='this.GetLoginSubTitle=..=>null'
subtitlecontent='This is a prototype of the upcoming Green Algorithms Dashboard. Using mock data, it allows you to see what the dashboard could look like if installed on your computing infrastructure. The goal is to enable users of Digital Research Infrastructures to understand and monitor the energy usage and environmental impacts of the computing tasks they run. Log in: User name: uid_1 \| Password: user1'
subtitle="this.GetLoginSubTitle=()=>'${subtitlecontent}'"
find $g_dir -name *.js \
    -exec sed -i "s|${subtitle2replace}|${subtitle}|g" {} \; \

# Email or username
find $g_dir -name *.js \
    -exec sed -i 's|Email or username"|Email or username (e.g. uid_1)"|g' {} \; \
    -exec sed -i 's|Password"|Password (e.g. user1)"|g' {} \; \