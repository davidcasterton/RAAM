clear all;
close all;
%load source .csv file
M = csvread('RAAM2012-Track_with_elev.csv');

%start row in .csv file
i_start = 2;
%end row in .csv file
i_end = size(M,1);
%time station locations in miles
%time_stations = [57.2,145.7,235.3,286.6,342.6,395,441.3,482.5,535.8,607.5,679.3,724.0,763.6,813.7,857.6,911.9,959.7,1006.3,1064.6,1129.6,1200.9,1269.6,1323.4,1373.5,1439.6,1471.6,1548.3,1582.5,1647,1706,1772.4,1821.4,1878.5,1955.3,2027.9,2074,2123.2,2195.9,2263.2,2326.4,2376,2426.2,2484.3,2543.3,2609.9,2674.8,2744.1,2772.6,2809.6,2858,2898.3,2934.9,2974.3,2983.8,2989.5];
time_stations = [56.8,145.2,234.9,286.3,342.3,395,441.1,482.7,536.1,608,679.8,724.6,764.2,814.4,858.6,912.9,960.9,1007.5,1065.8,1131.2,1202.6,1270.9,1325.1,1375.3,1441.4,1473.5,1550.3,1584.3,1648.9,1707.9,1774.3,1823.4,1880.8,1957.6,2030,2076.1,2125.3,2198.1,2265.5,2328.7,2378.2,2428.5,2486.6,2545.8,2612.5,2677.8,2747.7,2776.3,2813.4,2861.9,2902.2,2938.8,2978.3,2987.8,2993.5];
%time station locations in feet
time_stations_feet = time_stations .* 5280;
%time station locations in meters
time_stations_m = time_stations .* 1609.344;
%time station GPS + names
time_station_names = autodataread('RAAM2012-Time-Stations.csv');
%row of source .csv corresponding to time station change
time_station_row(1) = 1;
%current time station being processed
i_ts = 1;
%initialize run_total, which tracks waypoints distance on course
run_total(i_start-1) = 0;

% ----------
% calculate rise, run, and grade between each GPS waypoint
% ----------
for row=i_start:i_end,
    %elevation in feet
    elev(row) = M(row,3)*3.2808399;
    %run between waypoint in meters
    run(row) = gps_convert(M(row-1,1), M(row,1), M(row-1,2), M(row,2), M(row,3));
    %rise between waypoints in meters
    rise(row) = M(row,3) - M(row-1,3);
    %total distance on course in meters
    if run(row)<=0
        run_total(row) = run_total(row-1) + 0.0001;
    else
        run_total(row) = run_total(row-1) + run(row);
    end
    %grade since last waypoint
    grade(row) = 100*rise(row)/run(row);
    
    %check if passed time station
    if i_ts <= size(time_stations_m,2)
        if run_total(row) > time_stations_m(i_ts)
            i_ts = i_ts + 1;
            time_station_row(i_ts) = row;
        end
    end
end

time_station_row(i_ts) = row;
%run_total is total distance of each waypoint on course. this converts it from meters -> feet -> miles
run_total = run_total.*(3.2808399/5280);

%smooth grade
%smooth_grade = sgolayfilt(grade, 2, 15);
smooth_grade = grade;

mile_fraction = [4;8];
%calculate average grade per half mile
boxed_run = zeros(size(mile_fraction,1),size(run_total,2));
boxed_rise = zeros(size(mile_fraction,1),size(run_total,2));
boxed_grade = zeros(size(mile_fraction,1),size(run_total,2));
for f=1:size(mile_fraction,1)
    for row=i_start:i_end,
        mile = round(run_total(row)*mile_fraction(f));
        if mile == 0
            mile = 1;
        end
        boxed_run(f,mile) = boxed_run(f,mile) + run(row);
        boxed_rise(f,mile) = boxed_rise(f,mile) + rise(row);
    end
    boxed_grade(f,:) = 100.*boxed_rise(f,:)./boxed_run(f,:);
end

% ----------
% plot and save file of entire course
% ----------
% h = figure;
% subplot(2,1,1);
% plot(run_total(i_start:i_end), elev(i_start:i_end));
% title(horzcat('RAAM 2012. ',num2str(round(run_total(i_end)-run_total(i_start))),' miles.'));
% xlabel('course mile');
% ylabel('elevation (ft)');
% xlim([run_total(i_start) run_total(i_end)]);
% grid on
% grid minor
% subplot(2,1,2);
% x = 0.5:0.5:(size(boxed_grade,2)/2);
% plot_h = plot(x, boxed_grade);
% hold on
% % red = grade(i_start:i_end).*(grade(i_start:i_end)>=8);
% % bar_h1 = bar(run_total(i_start:i_end), red,  1, 'r', 'LineWidth', 2);
% red = boxed_grade.*(boxed_grade>=5);
% bar_h1 = bar(x, red, 'r');
% set(bar_h1, 'EdgeColor', 'r');
% title('% grade vs mile.');
% legend([bar_h1], '>5%')
% xlabel('course mile');
% ylabel('% grade');
% xlim([run_total(i_start) run_total(i_end)]);
% ylim([-15 15]);
% grid on
% grid minor
% set(gcf,'PaperPositionMode','auto');
% set(h,'Position',[10 10 2500 800]);
% print('-djpeg','-r300',strcat('total',num2str(i_ts),'.jpeg'));
% close(h)


% ----------
% plot and save file of each time station
% ----------
num_graphs = 1 + size(mile_fraction,1);
grade_axis_max = 10;
colorbar_axis_max = 15;
%size(time_station_row,2)-1
for i_ts=1:size(time_station_row,2)-1
    %start .csv row for this timestation
    i_start = time_station_row(i_ts);
    %ending .csv row for this timestation
    i_end = time_station_row(i_ts+1);
    %length of timestation in miles
    ts_miles = run_total(i_end)-run_total(i_start);
    %x-axis location for each waypoint
    x = run_total(i_start:i_end) - run_total(i_start);
    
    % ----------
    % elevation profile
    % ----------
    h=figure;
    sp(1) = subplot(num_graphs,1,1);
    plot(x, elev(i_start:i_end), 'LineWidth', 1);
    title(strcat(time_station_names.Name(i_ts),{'  -  '},time_station_names.Name(i_ts+1),{'.   '},num2str(ts_miles,'%.1f'),{' miles.'}));
    %define axis, etc.
    %xlabel('TS mile');
    ylabel('elevation (ft)');
    xlim([0 ts_miles]);
    elev_min = min(elev(i_start:i_end));
    ylim([elev_min elev_min+4500]);
    grid on
    grid minor
    pos(1,:) = get(sp(1), 'Position');
    
    % ----------
    % grade of each waypoint per fraction mile
    % ----------
    for f=1:size(mile_fraction,1)
        sp(1+f) = subplot(num_graphs,1,1+f);
        fraction = mile_fraction(f);
        x2 = 0:1/fraction:(run_total(i_end)-run_total(i_start));
        mileX2_start = round(run_total(i_start)*fraction);
        %matlab can't access 0 index, define start to 1
        if mileX2_start == 0
            mileX2_start = 1;
        end
        mileX2_end = mileX2_start + size(x2,2) - 1;
        bar_h6 = bar(x2, boxed_grade( f, mileX2_start : mileX2_end ) , 1);
        bar_child6=get(bar_h6,'Children');
        set(bar_child6, 'EdgeColor', 'b');
        set(bar_child6, 'CData', boxed_grade( f, mileX2_start : mileX2_end ));
        %define axis, etc.
        %title(horzcat('% grade averaged per 1/',num2str(fraction),' mile'));
        colorbar;
        caxis([-colorbar_axis_max colorbar_axis_max])
        ylabel({'% grade per',strcat('1/',num2str(fraction),' mile')});
        xlim([0 ts_miles]);
        ylim([-grade_axis_max grade_axis_max]);
        grid on
        grid minor
        pos(1+f,:) = get(sp(1+f), 'Position');
    end
    
%     % ----------
%     % grade of each waypoint, color coded in regions
%     % ----------
%     WP_plot_num = 2+size(mile_fraction,1);
%     sp(WP_plot_num) = subplot(num_graphs,1,WP_plot_num);
%     below_zero = smooth_grade(i_start:i_end).*(smooth_grade(i_start:i_end)<0);
%     bar_h4 = bar(x, below_zero, 1, 'c', 'LineWidth', 1);
%     set(bar_h4, 'EdgeColor', 'c');
%     hold on
%     above_zero = smooth_grade(i_start:i_end).*(smooth_grade(i_start:i_end)>0);
%     bar_h3 = bar(x, above_zero, 1, 'g', 'LineWidth', 1);
%     set(bar_h3, 'EdgeColor', 'g');
%     hold on
%     above_four = smooth_grade(i_start:i_end).*(smooth_grade(i_start:i_end)>=4);
%     bar_h1 = bar(x, above_four, 1, 'y', 'LineWidth', 1);
%     set(bar_h1, 'EdgeColor', 'y');
%     hold on
%     above_eight = smooth_grade(i_start:i_end).*(smooth_grade(i_start:i_end)>=8);
%     bar_h2 = bar(x, above_eight, 1, 'r', 'LineWidth', 2);
%     set(bar_h2, 'EdgeColor', 'r');
%     hold on
%     plot_h = plot(x, smooth_grade(i_start:i_end), 'LineWidth', 1);
%     %define axis, etc.
%     legend([bar_h2, bar_h1, bar_h3, bar_h4], '>8%','4-8%','0-4%','<0%','Location','NorthEastOutside')
%     %title('%grade between each waypoint')
%     %xlabel('TS mile');
%     ylabel({'% grade per','GPS waypoint'});
%     xlabel('TS mile');
%     xlim([0 ts_miles]);
%     ylim([-grade_axis_max grade_axis_max]);
%     grid on
%     grid minor
%     pos(WP_plot_num,:) = get(sp(WP_plot_num), 'Position');
    
    % ----------
    % reformat entire figure
    % ----------
    %scale x-axis of first and last subplots
    pos(1,3) = pos(3,3);
    set(sp(1),'Position',pos(1,:));
%     pos(num_graphs,3) = pos(3,3);
%     set(sp(num_graphs),'Position',pos(num_graphs,:));
    %remove tick labels for all but lowest plot
    for f=1:1 + size(mile_fraction,1) - 1
        set(sp(f),'XTickLabel','');
    end
    %remove y spacing between plots
    for f=2:1 + size(mile_fraction,1)
        pos(f,2) = pos(f-1,2) - pos(f,4) - .015;
        set(sp(f),'Position',pos(f,:))
    end
    
    % ----------
    % save to file
    % ----------
    %set(gca,'LooseInset',get(gca,'TightInset'))
    set(gcf,'PaperPositionMode','auto');
    set(h,'Position',[10 10 1700 750]);
    %print('-djpeg','-r300',strcat('TS',num2str(i_ts),'.jpeg'));
    savefig(strcat('graphs\TS',num2str(i_ts)), 'pdf', '-r300')
    %close window
    close(h)
end