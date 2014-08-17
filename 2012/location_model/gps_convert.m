function distance_m = gps_convert(lat1,lat2,long1,long2,h)

maj_const=6378137;          %Major axis constant
min_const=6356752.3142;     %Minor axis constant
%h=334.9;                    %Elevation

% True angle determination (atan=ArcTan)
angle1=(atan((min_const^2)/(maj_const^2)*tan(lat1*pi()/180)))*180/pi();
angle2=(atan((min_const^2)/(maj_const^2)*tan(lat2*pi()/180)))*180/pi();

% Radius calculation for the two points
r1=(1/((cos(angle1*pi()/180))^2/maj_const^2+(sin(angle1*pi()/180))^2/min_const^2))^0.5+h;
r2=(1/((cos(angle2*pi()/180))^2/maj_const^2+(sin(angle2*pi()/180))^2/min_const^2))^0.5+h;

% X-Y earth coordinates
xy1=r1*cos(angle1*pi()/180);
xy2=r2*cos(angle2*pi()/180);
xy3=r1*sin(angle1*pi()/180);
xy4=r2*sin(angle2*pi()/180);

X=((xy1-xy2)^2+(xy3-xy4)^2)^0.5;         % X coordinate
Y=2*pi()*((((xy1+xy2)/2))/360)*(long1-long2);     % Y coordinate

format short                             % Switch to short format

distance_m=((X)^2+(Y)^2)^0.5;                    % Distance Meter
distance_ft= distance_m*3.28084;                    % Distance feet