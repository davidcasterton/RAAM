clear all;
close all;

%time station locations in miles
TS_mile = [0,56.8,145.2,234.9,286.3,342.3,395,441.1,482.7,536.1,608,679.8,724.6,764.2,814.4,858.6,912.9,960.9,1007.5,1065.8,1131.2,1202.6,1270.9,1325.1,1375.3,1441.4,1473.5,1550.3,1584.3,1648.9,1707.9,1774.3,1823.4,1880.8,1957.6,2030,2076.1,2125.3,2198.1,2265.5,2328.7,2378.2,2428.5,2486.6,2545.8,2612.5,2677.8,2747.7,2776.3,2813.4,2861.9,2902.2,2938.8,2978.3,2987.8,2993.5];
%load Barrie's time station mph estimate. 4 updated through TS14
Barrie = csvread('Calcs_2012_4.csv');
%time station GPS + names
TS_name = autodataread('RAAM2012-Time-Stations.csv');

start_hr = 16;
csv = cell(150,5);

csv{1,1} = 'race hour';
csv{1,2} = 'EST';
csv{1,3} = 'local time';
csv{1,4} = 'course mile';
csv{1,5} = 'TS mph';
csv{1,6} = 'team';
csv{1,7} = 'location';

csv{2,1} = 0; %race hour
csv{2,2} = start_hr; %eastern time
csv{2,3} = start_hr-3; %local time
csv{2,4} = 0; %course mile
csv{2,5} = Barrie(1); %mph
csv{2,6} = 1; %team
csv{2,7} = strcat(TS_name.Name(1)); %location

hr = 1;
TS_next = 1;
team = 0;
team_count = 1;
while TS_next < size(Barrie,1),
    idx = hr + 2;
    
    csv{idx,1} = hr; %race hour
    csv{idx,2} = mod(start_hr + hr, 24); %eastern time
    csv{idx,4} = csv{idx-1,4}; %course mile
    csv{idx,5} = Barrie(TS_next); %TS mph
    for i=1:10,
        csv{idx,4} = csv{idx,4} + Barrie(TS_next)/10; %course mile
        %update last TS
        if csv{idx,4} > TS_mile(TS_next+1),
            TS_next = TS_next + 1;
        end
        if TS_next > size(Barrie,1),
            break
        end
    end
    
    %local time
    if TS_next-1 <= 11,
        csv{idx,3} = csv{idx,2} - 3;
    elseif TS_next-1 <= 23,
        csv{idx,3} = csv{idx,2} - 2;
    elseif TS_next-1 <= 38,
        csv{idx,3} = csv{idx,2} - 1;
    else
        csv{idx,3} = csv{idx,2};
    end
    switch csv{idx,3}
        case -1
            csv{idx,3} = 23;
        case -2
            csv{idx,3} = 22;
        case -3
            csv{idx,3} = 21;
    end
    
    %team
    if team_count >= 5,
        team = mod(team+1,4);
        team_count = 0;
    end
    csv{idx,6} = team+1;
    team_count = team_count + 1;
    
    csv{idx,7} = strcat(TS_name.Name(TS_next),' + ',num2str(round( csv{idx,4}-TS_mile(TS_next) )),'mi'); %location
    
    hr = hr + 1;
end
idx = idx + 1;
csv{idx,1} = hr;
csv{idx,2} = mod(start_hr + hr, 24);
csv{idx,3} = csv{idx,2};
csv{idx,4} = TS_mile(56);
csv{idx,5} = Barrie(55);
csv{idx,7} = TS_name.Name(56);

dlmcell('hour_mile.csv',csv,',');