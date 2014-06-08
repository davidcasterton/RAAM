function [data]=autodataread(fname)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This function reads an ASCII delimted data file containing mixed data (numeric %
% and text columns)and returns the column headings as variables in a structured  %
% array containing the data in column vectors of mixed type. Text columns and    %
% data types are autodetected. Duplicate columns are detected and eliminated.    %
% Delimiter type is autodetected (supports tab, space, or comma). Supported file %
% extensions include .xls, .csv, .asc, .txt and others.                          %
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
% There is a parameter association block that renames common input parameters    %
% with names of your chosing .                                                   %          
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Written by Scott Burnside, United States Air Force, 2002                       %
% Phone: (661) 277-4282, Email: richard.burnside@edwards.af.mil                  %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% The function is called with the file name as an input and returns a structured %
% array "data" with parameters defined as "data.parameter".                      %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This code utilizes an undocumented Matlab function dataread.dll. The author    %
% assumes no responsibility for future compatibility. The Mathworks can alter    %
% dataread.dll at any time without notice which could render this function       %
% inoperative. You have been warned.                                             %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
format long g
global data;
fid = fname;
% get the number of rows
[row_test] = dataread('file',fid,'%f%*[^\n]','delimiter',',', 'headerlines',1);
[num_rows, colm] = size(row_test);
clear colm;
merge_file = fopen(fid,'r');
%retrieve column headers
headers = fgetl(merge_file);
% get a sample data line
samp = fgetl(merge_file);
fclose(merge_file);
u = double(samp);
clear samp;
k = double(headers);
z = length(u);
g = length(k);
% strip the commas out of the sample data line and headerline
u(u==44)=32;
k(k==44)=32;
% cleanup
clear z;
clear s;
orin = char(u);
clear u;
roy = char(k);
clear k;
% parse headerline and sample data line
roger = 0;
sampcell = gleanheader(roger,orin);
headercell = gleanheader(roger,roy);
[rw, cl] = size(headercell);
if cl == 1;
    roger = 1;
    sampcell = gleanheader(roger,orin);
    headercell = gleanheader(roger,roy);
end
% get the number of columns
num_cols = length(headercell);
% eliminate duplicate columns
[b,ndx,pos] = unique(headercell);
bust = length(b);
%
%--------------Input Parameter Association Block-----------------------------
%
% the following short input parmeters are replaced with associated long names
%
b=param_associate(b,'FTime','Time'); % Should be FTime for Tom data and RTime for Mux data
b=param_associate(b,'STN','Source_Track_Number'); 
b=param_associate(b,'Trigger','J_Message_Type');
b=param_associate(b,'TimeQual','Time_Quality');
b=param_associate(b,'GeoQual','Geodetic_Quality');
b=param_associate(b,'AltQual','Altitude_Quality');
b=param_associate(b,'NPS_Ind','Network_Participation_Status');
b=param_associate(b,'Altitude','PPLI_Altitude');
b=param_associate(b,'Latitude','PPLI_Latitude');
b=param_associate(b,'Longitude','PPLI_Longitude');
b=param_associate(b,'Speed','PPLI_Speed');
b=param_associate(b,'Course','PPLI_Course');
b=param_associate(b,'FLIndic','Flight_Leader_Indicator');
b=param_associate(b,'ABIndic','Airborne_Indicator');
b=param_associate(b,'TRHDG','True_Heading');
b=param_associate(b,'DRLAT','MIDS_Latitude');
b=param_associate(b,'DRLONG','MIDS_Longitude');
b=param_associate(b,'MSLALT','MIDS_Altitude');
b=param_associate(b,'VELX','MIDS_Velocity_X');
b=param_associate(b,'VELY','MIDS_Velocity_Y');
b=param_associate(b,'VELZ','MIDS_Velocity_Z');
b=param_associate(b,'CXZ','INS_CXZ_Latitude');
b=param_associate(b,'LONG','INS_Longitude');
b=param_associate(b,'ALTINERT','INS_Altitude');
b=param_associate(b,'VX','INS_Velocity_X');
b=param_associate(b,'VY','INS_Velocity_Y');
b=param_associate(b,'VZ','INS_Velocity_Z');
b=param_associate(b,'TLAT','TSPI_Latitude');
b=param_associate(b,'TLONG','TSPI_Longitude');
b=param_associate(b,'TALT','TSPI_Altitude');
b=param_associate(b,'THGT','TSPI_Ellipsoid_Height');
b=param_associate(b,'TVX','TSPI_Velocity_X');
b=param_associate(b,'TVY','TSPI_Velocity_Y');
b=param_associate(b,'TVZ','TSPI_Velocity_Z');
%
% reorder columns into ASCII dictionary order
arcwing = 1;
trt = 1:num_cols;
ralphy = setdiff(trt,ndx);
catbreath = 1;
for dogbreath = 1:num_cols;
     if (ismember(arcwing,ralphy)==0);
          rosco(catbreath)=(b(ndx==arcwing));
          arcwing = arcwing + 1;
          catbreath = catbreath + 1;
     else
          arcwing = arcwing + 1;
     end
end
%
% rebuild headercolumn names with associations
kipper=1;
for relp=1:bust;
     bugwater(pos==kipper)=b(kipper);
     kipper=kipper+1;
end
headercell=bugwater;
%
% define string pieces for file read command string builder
data_format = '';
read_str = '%s';
read_num = '%f';
read_format = '[';
spacer = ',';
for xc=1:num_cols % % build read command input format and output format strings by testing column data types
    [tmp,ct,errmsg] = sscanf(sampcell{xc},'%f');
    if( length(errmsg) > 0 )
        data_format = strcat(data_format,read_str); % Read String
    else
        data_format = strcat(data_format,read_num); % Read Number
    end
    read_format = strcat(read_format,'data.',char(headercell(xc)),spacer);
end
% read the data
cmd_suffix = '] = dataread(''file'',fid,data_format,num_rows,''delimiter'','','', ''headerlines'', 1);';
read_format = strcat(read_format(1:(end-1)),cmd_suffix);
eval(read_format);
data.names = rosco;
data.num_params = length(data.names);
return

function names = gleanheader(roger,tempstr)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This subfunction parses the headerline and returns the column headings as variables %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if roger == 1;
    ch = char(9); % header delimiting character definition is Tab
else
    ch = char(32); % header delimiting character definition is Comma
end
index = 0;
while length(tempstr > 0) % separate objects based on delimiter positions
     index = index + 1;
     tempstr = fliplr(deblank(fliplr(deblank(tempstr))));
     if isempty(find(tempstr == ch))
          names{index} = tempstr;
          tempstr = [];
     else
          names{index} = tempstr(1:find(tempstr == ch)-1);
          tempstr(1:find(tempstr == ch)) = [];
     end  
end
return
 
function b = param_associate(b,short_name,long_name)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This subfunction replaces column heading names with pre-defined long names %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if isempty(STRMATCH(short_name,b,'exact'))==0;
      b{STRMATCH(short_name,b,'exact')} = long_name;
end
return