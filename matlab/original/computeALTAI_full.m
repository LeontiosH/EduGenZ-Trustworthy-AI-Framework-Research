function [inst, relation, gender, mainCatNames_sorted, mainMeans_sorted, mainCIs_sorted, subCatNames_sorted, subMeans_sorted, subCIs_sorted] = computeALTAI_full(filename)
% computeALTAI_full
% Complete ALTAI analysis with:
% - Metadata extraction
% - Main category statistics (7)
% - Subcategory statistics (19)
% - Sorted outputs
% - Main-category plot with 95% CI + mean labels (collision-free)
% - Subcategory plot with 95% CI + mean labels + main-category colors + legend
% [inst, relation, gender,mainCatNames_sorted, mainMeans_sorted, mainCIs_sorted, subCatNames_sorted, subMeans_sorted, subCIs_sorted] = computeALTAI_full('EduGenZDataAnalysis11_USETHIS4ANALYSIS.xlsx');
% this works fine and used for the D2.3 figures
% LJH 25.3.2026

% ---------------------------------------------------------
% LOAD RAW DATA
% ---------------------------------------------------------
raw = readcell(filename);

% ---------------------------------------------------------
% METADATA (start at row 5)
% ---------------------------------------------------------
inst     = raw(5:end, 2);
relation = raw(5:end, 3);
gender   = raw(5:end, 4);

% ---------------------------------------------------------
% ALTAI BLOCK (columns E:CJ)
% ---------------------------------------------------------
ALTAI = raw(:, 5:88);

% ---------------------------------------------------------
% HEADERS
% ---------------------------------------------------------
mainCats = ALTAI(1, :);   % 7 main categories
rawSub   = ALTAI(2, :);   % 19 subcategories

% ---------------------------------------------------------
% FORCE SUBCATEGORIES TO STRINGS
% ---------------------------------------------------------
subCats = strings(1, numel(rawSub));
for c = 1:numel(rawSub)
    val = rawSub{c};
    if isempty(val) || (isnumeric(val) && isnan(val))
        subCats(c) = "";
    else
        subCats(c) = string(val);
    end
end
subCats = strtrim(subCats);
subCats = cellstr(subCats);

% ---------------------------------------------------------
% NUMERIC DATA (start at row 5)
% ---------------------------------------------------------
data = ALTAI(5:end, :);
numericData = cellfun(@(x) str2double(string(x)), data);
numericData(numericData < 1 | numericData > 3) = NaN;

% =========================================================
% MAIN CATEGORY STATISTICS (7)
% =========================================================
mainCatNames = unique(mainCats, 'stable');
nMain = length(mainCatNames);

mainMeans = zeros(nMain, 1);
mainCIs   = zeros(nMain, 1);

for i = 1:nMain
    cols = strcmp(mainCats, mainCatNames{i});
    values = numericData(:, cols);
    values = values(values >= 1 & values <= 3);

    if isempty(values)
        mainMeans(i) = NaN;
        mainCIs(i)   = NaN;
    else
        m  = mean(values);
        sd = std(values);
        n  = length(values);
        ci = 1.96 * sd / sqrt(n);

        mainMeans(i) = m  * (10/3);
        mainCIs(i)   = ci * (10/3);
    end
end

% SORT MAIN CATEGORIES
[mainMeans_sorted, idxMain] = sort(mainMeans, 'descend');
mainCatNames_sorted = mainCatNames(idxMain)';
mainCIs_sorted      = mainCIs(idxMain);

% =========================================================
% SUBCATEGORY STATISTICS (19)
% =========================================================
subCatNames = unique(subCats, 'stable');
nSub = length(subCatNames);

subMeans = zeros(nSub, 1);
subCIs   = zeros(nSub, 1);

for i = 1:nSub
    cols = strcmp(subCats, subCatNames{i});
    values = numericData(:, cols);
    values = values(values >= 1 & values <= 3);

    if isempty(values)
        subMeans(i) = NaN;
        subCIs(i)   = NaN;
    else
        m  = mean(values);
        sd = std(values);
        n  = length(values);
        ci = 1.96 * sd / sqrt(n);

        subMeans(i) = m  * (10/3);
        subCIs(i)   = ci * (10/3);
    end
end

% SORT SUBCATEGORIES
[subMeans_sorted, idxSub] = sort(subMeans, 'descend');
subCatNames_sorted = subCatNames(idxSub)';
subCIs_sorted      = subCIs(idxSub);

%% ============================================================
% BUILD MAIN-CATEGORY COLOR MAP (used in BOTH figures)
% ============================================================

mainCatNames_unique = unique(mainCats, 'stable');
nMain = numel(mainCatNames_unique);

% 7 distinct colors
mainColors = lines(nMain);

% Map: main category → RGB color
mainColorMap = containers.Map;
for i = 1:nMain
    mainColorMap(mainCatNames_unique{i}) = mainColors(i,:);
end
%% ============================================================
% FIGURE 1 — MAIN CATEGORIES (with main-category colors)
% ============================================================

figure('Color','w','Position',[200 200 900 700]);

% Build color array for sorted main categories
mainColors_sorted = zeros(numel(mainCatNames_sorted), 3);
for i = 1:numel(mainCatNames_sorted)
    mainColors_sorted(i,:) = mainColorMap(mainCatNames_sorted{i});
end

% Horizontal bar plot
b = barh(mainMeans_sorted, 'FaceColor','flat'); hold on;

for k = 1:numel(mainMeans_sorted)
    b.CData(k,:) = mainColors_sorted(k,:);
end

% Error bars
errorbar(mainMeans_sorted, 1:numel(mainMeans_sorted), ...
    mainCIs_sorted, 'horizontal', ...
    'LineStyle','none','Color','k','LineWidth',1.2);

% Collision-free mean labels
for k = 1:numel(mainMeans_sorted)
    offset = mainCIs_sorted(k) + 0.25;
    text(mainMeans_sorted(k) + offset, k, sprintf('%.2f', mainMeans_sorted(k)), ...
        'VerticalAlignment','middle', 'FontSize', 11, 'FontWeight','bold');
end

set(gca, 'YTick', 1:numel(mainMeans_sorted), ...
    'YTickLabel', mainCatNames_sorted, ...
    'FontSize', 12, 'FontWeight','bold', ...
    'YDir','reverse');

xlabel('Importance Score', 'FontSize', 12);
title('ALTAI Main Categories — Mean Score with 95% CI', ...
    'FontSize', 14, 'FontWeight','bold');

xlim([1 10]);
xticks(1:10);

grid on; box off;

% =========================================================
% FIGURE 2 — SUBCATEGORIES
% =========================================================

% Map subcategory → main category
subToMain = containers.Map;
for c = 1:numel(subCats)
    subToMain(subCats{c}) = mainCats{c};
end

% Assign each main category a unique color
mainCatNames_unique = unique(mainCats, 'stable');
nMain = numel(mainCatNames_unique);
mainColors = lines(nMain);

mainColorMap = containers.Map;
for i = 1:nMain
    mainColorMap(mainCatNames_unique{i}) = mainColors(i,:);
end

% Build color array for sorted subcategories
subColors = zeros(numel(subCatNames_sorted), 3);
for i = 1:numel(subCatNames_sorted)
    sc = subCatNames_sorted{i};
    parentMain = subToMain(sc);
    subColors(i,:) = mainColorMap(parentMain);
end

% Plot
figure('Color','w','Position',[200 200 900 700]);

b = barh(subMeans_sorted, 'FaceColor','flat'); hold on;

for k = 1:numel(subMeans_sorted)
    b.CData(k,:) = subColors(k,:);
end

% Error bars
errorbar(subMeans_sorted, 1:numel(subMeans_sorted), ...
    subCIs_sorted, 'horizontal', ...
    'LineStyle','none','Color','k','LineWidth',1.2);

% Collision-free mean labels
for k = 1:numel(subMeans_sorted)
    offset = subCIs_sorted(k) + 0.25;
    text(subMeans_sorted(k) + offset, k, sprintf('%.2f', subMeans_sorted(k)), ...
        'VerticalAlignment','middle', 'FontSize', 11, 'FontWeight','bold');
end

set(gca, 'YTick', 1:numel(subMeans_sorted), ...
    'YTickLabel', subCatNames_sorted, ...
    'FontSize', 12, 'FontWeight','bold', ...
    'YDir','reverse');

xlabel('Importance Score', 'FontSize', 12);
title('ALTAI Subcategories — Mean Score with 95% CI', ...
    'FontSize', 14, 'FontWeight','bold');
xlim([1 10]);
xticks(1:10);

grid on; box off;

% Legend
hold on;
legendHandles = gobjects(nMain,1);
for i = 1:nMain
    legendHandles(i) = plot(NaN, NaN, 's', ...
        'MarkerFaceColor', mainColors(i,:), ...
        'MarkerEdgeColor', 'k', ...
        'MarkerSize', 12);
end

legend(legendHandles, mainCatNames_unique, ...
    'Location','eastoutside', ...
    'FontSize', 12, 'FontWeight','bold');

%% ============================================================
% SAVE FIGURES AND PARAMETERS
% ============================================================

% Create output names based on filename
[~, baseName, ~] = fileparts(filename);

% Figure 1 filenames
fig1_name = sprintf('%s_mainCategories.fig', baseName);
png1_name = sprintf('%s_mainCategories.png', baseName);

% Figure 2 filenames
fig2_name = sprintf('%s_subCategories.fig', baseName);
png2_name = sprintf('%s_subCategories.png', baseName);

% Save figures
savefig(1, fig1_name);
saveas(1, png1_name);

savefig(2, fig2_name);
saveas(2, png2_name);

% Save all computed parameters
mat_name = sprintf('%s_ALTAI_results.mat', baseName);

save(mat_name, ...
    'inst', 'relation', 'gender', ...
    'mainCatNames_sorted', 'mainMeans_sorted', 'mainCIs_sorted', ...
    'subCatNames_sorted', 'subMeans_sorted', 'subCIs_sorted');

% % % % %% ============================================================
% % % % % FINAL: REGRESSION + NON-PARAMETRIC TESTS + EFFECT SIZES + VISUALS
% % % % % ============================================================
% % % %
% % % % %% ============================================================
% % % % % NON-PARAMETRIC TESTS FOR ALL COVARIATES + BOXPLOTS
% % % % % ============================================================
% % % %
% % % % %% ------------------------------------------------------------
% % % % % 1. Unique category names (stable order)
% % % % % ------------------------------------------------------------
% % % % mainCatNames_unique = unique(mainCats, 'stable');
% % % % subCatNames_unique  = unique(subCats,  'stable');
% % % %
% % % % nMain = numel(mainCatNames_unique);
% % % % nSub  = numel(subCatNames_unique);
% % % % nObs  = numel(inst);
% % % %
% % % % inst_cat     = categorical(inst);
% % % % relation_cat = categorical(relation);
% % % % gender_cat   = categorical(gender);
% % % %
% % % % %% ------------------------------------------------------------
% % % % % 2. Build subject-level scores
% % % % % ------------------------------------------------------------
% % % % mainScores = nan(nObs, nMain);
% % % % for i = 1:nMain
% % % %     cols = strcmp(mainCats, mainCatNames_unique{i});
% % % %     mainScores(:, i) = mean(numericData(:, cols), 2, 'omitnan') * (10/3);
% % % % end
% % % %
% % % % subScores = nan(nObs, nSub);
% % % % for i = 1:nSub
% % % %     cols = strcmp(subCats, subCatNames_unique{i});
% % % %     subScores(:, i) = mean(numericData(:, cols), 2, 'omitnan') * (10/3);
% % % % end
% % % %
% % % % %% ------------------------------------------------------------
% % % % % 3. Non-parametric p-values for ALL covariates
% % % % % ------------------------------------------------------------
% % % % mainP_gender      = strings(nMain,1);
% % % % mainP_institution = strings(nMain,1);
% % % % mainP_relation    = strings(nMain,1);
% % % %
% % % % subP_gender      = strings(nSub,1);
% % % % subP_institution = strings(nSub,1);
% % % % subP_relation    = strings(nSub,1);
% % % %
% % % % for i = 1:nMain
% % % %     scores = mainScores(:,i);
% % % %
% % % %     % Gender (2 groups → Mann–Whitney)
% % % %     g1 = scores(gender_cat=='male');   g1 = g1(~isnan(g1));
% % % %     g2 = scores(gender_cat=='female'); g2 = g2(~isnan(g2));
% % % %     if numel(g1)>=2 && numel(g2)>=2 && ~(std(g1)==0 && std(g2)==0)
% % % %         p = ranksum(g1,g2);
% % % %         mainP_gender(i) = sprintf('%.3f', p);
% % % %     else
% % % %         mainP_gender(i) = "NS";
% % % %     end
% % % %
% % % %     % Institution (k groups → Kruskal–Wallis)
% % % %     try
% % % %         p = kruskalwallis(scores, inst_cat, 'off');
% % % %         mainP_institution(i) = sprintf('%.3f', p);
% % % %     catch
% % % %         mainP_institution(i) = "NS";
% % % %     end
% % % %
% % % %     % Relation (k groups → Kruskal–Wallis)
% % % %     try
% % % %         p = kruskalwallis(scores, relation_cat, 'off');
% % % %         mainP_relation(i) = sprintf('%.3f', p);
% % % %     catch
% % % %         mainP_relation(i) = "NS";
% % % %     end
% % % % end
% % % %
% % % % for i = 1:nSub
% % % %     scores = subScores(:,i);
% % % %
% % % %     % Gender
% % % %     g1 = scores(gender_cat=='male');   g1 = g1(~isnan(g1));
% % % %     g2 = scores(gender_cat=='female'); g2 = g2(~isnan(g2));
% % % %     if numel(g1)>=2 && numel(g2)>=2 && ~(std(g1)==0 && std(g2)==0)
% % % %         p = ranksum(g1,g2);
% % % %         subP_gender(i) = sprintf('%.3f', p);
% % % %     else
% % % %         subP_gender(i) = "NS";
% % % %     end
% % % %
% % % %     % Institution
% % % %     try
% % % %         p = kruskalwallis(scores, inst_cat, 'off');
% % % %         subP_institution(i) = sprintf('%.3f', p);
% % % %     catch
% % % %         subP_institution(i) = "NS";
% % % %     end
% % % %
% % % %     % Relation
% % % %     try
% % % %         p = kruskalwallis(scores, relation_cat, 'off');
% % % %         subP_relation(i) = sprintf('%.3f', p);
% % % %     catch
% % % %         subP_relation(i) = "NS";
% % % %     end
% % % % end
% % % %
% % % % %% ------------------------------------------------------------
% % % % % 4. Summary tables
% % % % % ------------------------------------------------------------
% % % % MainCategoryStats = table( ...
% % % %     mainCatNames_unique(:), ...
% % % %     mainP_gender(:), mainP_institution(:), mainP_relation(:), ...
% % % %     'VariableNames', {'MainCategory','P_Gender','P_Institution','P_Relation'});
% % % %
% % % % SubCategoryStats = table( ...
% % % %     subCatNames_unique(:), ...
% % % %     subP_gender(:), subP_institution(:), subP_relation(:), ...
% % % %     'VariableNames', {'SubCategory','P_Gender','P_Institution','P_Relation'});
% % % %
% % % % %% ------------------------------------------------------------
% % % % % 5. BOXPLOTS — MAIN CATEGORIES (Gender, Institution, Relation)
% % % % % ------------------------------------------------------------
% % % % figure('Color','w','Position',[200 200 1600 900]);
% % % %
% % % % for i = 1:nMain
% % % %     scores = mainScores(:,i);
% % % %
% % % %     % --- Gender ---
% % % %     subplot(3, nMain, i)
% % % %     boxplot(scores, gender_cat)
% % % %     title(mainCatNames_unique{i}, 'FontWeight','bold')
% % % %     ylim([1 10])
% % % %     text(1.5, 2, mainP_gender(i), 'HorizontalAlignment','center','FontWeight','bold')
% % % %
% % % %     % --- Institution ---
% % % %     subplot(3, nMain, nMain + i)
% % % %     boxplot(scores, inst_cat)
% % % %     title(['Institution – ' mainCatNames_unique{i}], 'FontWeight','bold')
% % % %     ylim([1 10])
% % % %     text(1.5, 2, mainP_institution(i), 'HorizontalAlignment','center','FontWeight','bold')
% % % %
% % % %     % --- Relation ---
% % % %     subplot(3, nMain, 2*nMain + i)
% % % %     boxplot(scores, relation_cat)
% % % %     title(['Relation – ' mainCatNames_unique{i}], 'FontWeight','bold')
% % % %     ylim([1 10])
% % % %     text(1.5, 2, mainP_relation(i), 'HorizontalAlignment','center','FontWeight','bold')
% % % % end
% % % %
% % % % sgtitle('Main Categories – Gender, Institution, Relation', 'FontSize', 16, 'FontWeight','bold');
% % % %
% % % % %% ------------------------------------------------------------
% % % % % 6. BOXPLOTS — SUBCATEGORIES (Gender, Institution, Relation)
% % % % % ------------------------------------------------------------
% % % % figure('Color','w','Position',[200 200 1800 1200]);
% % % %
% % % % for i = 1:nSub
% % % %     scores = subScores(:,i);
% % % %
% % % %     % --- Gender ---
% % % %     subplot(3, nSub, i)
% % % %     boxplot(scores, gender_cat)
% % % %     title(subCatNames_unique{i}, 'FontWeight','bold')
% % % %     ylim([1 10])
% % % %     text(1.5, 2, subP_gender(i), 'HorizontalAlignment','center','FontWeight','bold')
% % % %
% % % %     % --- Institution ---
% % % %     subplot(3, nSub, nSub + i)
% % % %     boxplot(scores, inst_cat)
% % % %     title(['Institution – ' subCatNames_unique{i}], 'FontWeight','bold')
% % % %     ylim([1 10])
% % % %     text(1.5, 2, subP_institution(i), 'HorizontalAlignment','center','FontWeight','bold')
% % % %
% % % %     % --- Relation ---
% % % %     subplot(3, nSub, 2*nSub + i)
% % % %     boxplot(scores, relation_cat)
% % % %     title(['Relation – ' subCatNames_unique{i}], 'FontWeight','bold')
% % % %     ylim([1 10])
% % % %     text(1.5, 2, subP_relation(i), 'HorizontalAlignment','center','FontWeight','bold')
% % % % end
% % % %
% % % % sgtitle('Subcategories – Gender, Institution, Relation', 'FontSize', 16, 'FontWeight','bold');
% % % %
% % % % %% ------------------------------------------------------------
% % % % % 7. SAVE RESULTS
% % % % % ------------------------------------------------------------
% % % % [~,baseName,~] = fileparts(filename);
% % % % excel_name = sprintf('%s_ALTAI_stats.xlsx',  baseName);
% % % %
% % % % writetable(MainCategoryStats, excel_name, 'Sheet','Main');
% % % % writetable(SubCategoryStats,  excel_name, 'Sheet','Sub');

%% ============================================================
% ALTAI – FULL ANALYSIS PIPELINE
% ============================================================

%% ------------------------------------------------------------
% 0. BASIC SETUP
% ------------------------------------------------------------
nObs  = size(numericData, 1);
mainCatNames_unique = unique(mainCats, 'stable');
subCatNames_unique  = unique(subCats,  'stable');
nMain = numel(mainCatNames_unique);
nSub  = numel(subCatNames_unique);

inst_cat   = categorical(inst);
gender_cat = categorical(gender);

[~, baseName, ~] = fileparts(filename);

%% ------------------------------------------------------------
% RECODE RELATION INTO SHORT LABELS (robust)
% ------------------------------------------------------------
relation_cat = categorical(relation);

old = {'1','2','4','5','6'};
new = {'EGZ-m-tech','EGZ-m-edu','EGZ-m-stu','TStaff','Stu'};

for k = 1:numel(old)
    if any(relation_cat == old{k})
        relation_cat = renamecats(relation_cat, old{k}, new{k});
    end
end

%% ------------------------------------------------------------
% 1. SUBJECT-LEVEL SCORES (for plots & non-parametric tests)
% ------------------------------------------------------------
mainScores = nan(nObs, nMain);
for i = 1:nMain
    cols = strcmp(mainCats, mainCatNames_unique{i});
    mainScores(:, i) = mean(numericData(:, cols), 2, 'omitnan') * (10/3);
end

subScores = nan(nObs, nSub);
for i = 1:nSub
    cols = strcmp(subCats, subCatNames_unique{i});
    subScores(:, i) = mean(numericData(:, cols), 2, 'omitnan') * (10/3);
end

%% ------------------------------------------------------------
% 2. NON-PARAMETRIC P-VALUES
% ------------------------------------------------------------
mainP_gender      = strings(nMain,1);
mainP_institution = strings(nMain,1);
mainP_relation    = strings(nMain,1);

subP_gender      = strings(nSub,1);
subP_institution = strings(nSub,1);
subP_relation    = strings(nSub,1);

for i = 1:nMain
    scores = mainScores(:,i);

    % Gender
    g1 = scores(gender_cat=='male');   g1 = g1(~isnan(g1));
    g2 = scores(gender_cat=='female'); g2 = g2(~isnan(g2));
    if numel(g1)>=2 && numel(g2)>=2 && ~(std(g1)==0 && std(g2)==0)
        p = ranksum(g1,g2);
        mainP_gender(i) = sprintf('%.3f', p);
    else
        mainP_gender(i) = "N/A";
    end

    % Institution
    try
        p = kruskalwallis(scores, inst_cat, 'off');
        mainP_institution(i) = sprintf('%.3f', p);
    catch
        mainP_institution(i) = "N/A";
    end

    % Relation
    try
        p = kruskalwallis(scores, relation_cat, 'off');
        mainP_relation(i) = sprintf('%.3f', p);
    catch
        mainP_relation(i) = "N/A";
    end
end

for i = 1:nSub
    scores = subScores(:,i);

    % Gender
    g1 = scores(gender_cat=='male');   g1 = g1(~isnan(g1));
    g2 = scores(gender_cat=='female'); g2 = g2(~isnan(g2));
    if numel(g1)>=2 && numel(g2)>=2 && ~(std(g1)==0 && std(g2)==0)
        p = ranksum(g1,g2);
        subP_gender(i) = sprintf('%.3f', p);
    else
        subP_gender(i) = "N/A";
    end

    % Institution
    try
        p = kruskalwallis(scores, inst_cat, 'off');
        subP_institution(i) = sprintf('%.3f', p);
    catch
        subP_institution(i) = "N/A";
    end

    % Relation
    try
        p = kruskalwallis(scores, relation_cat, 'off');
        subP_relation(i) = sprintf('%.3f', p);
    catch
        subP_relation(i) = "N/A";
    end
end

%% ------------------------------------------------------------
% 3. SUMMARY TABLES
% ------------------------------------------------------------
MainCategoryStats = table( ...
    mainCatNames_unique(:), ...
    mainP_gender(:), mainP_institution(:), mainP_relation(:), ...
    'VariableNames', {'MainCategory','P_Gender','P_Institution','P_Relation'});

SubCategoryStats = table( ...
    subCatNames_unique(:), ...
    subP_gender(:), subP_institution(:), subP_relation(:), ...
    'VariableNames', {'SubCategory','P_Gender','P_Institution','P_Relation'});

%% ============================================================
% 4. BOXPLOTS – SIX FIGURES (MAIN + SUB × 3 COVARIATES)
% ============================================================

%% MAIN × GENDER
h = figure('Color','w','Position',[200 200 1600 900]);
for i = 1:nMain
    subplot(ceil(nMain/2), 2, i)
    boxplot(mainScores(:,i), gender_cat)
    title(mainCatNames_unique{i}, 'FontWeight','bold')
    ylabel('Score')
    ylim([1 10])
    mainP_gender(i)
    text(1.5, 2, mainP_gender(i), 'HorizontalAlignment','center','FontWeight','bold')
 end
sgtitle('Main Categories – Gender', 'FontSize', 16, 'FontWeight','bold');
saveFig(h, baseName, 'Main_Gender');

%% MAIN × INSTITUTION
h = figure('Color','w','Position',[200 200 1600 900]);
for i = 1:nMain
    subplot(ceil(nMain/2), 2, i)
    boxplot(mainScores(:,i), inst_cat)
    title(['Institution – ' mainCatNames_unique{i}], 'FontWeight','bold')
    ylabel('Score')
    ylim([1 10])

        text(1, 2, mainP_institution(i), 'HorizontalAlignment','left','FontWeight','bold')

end
sgtitle('Main Categories – Institution', 'FontSize', 16, 'FontWeight','bold');
saveFig(h, baseName, 'Main_Institution');

%% MAIN × RELATION
h = figure('Color','w','Position',[200 200 1600 900]);
for i = 1:nMain
    subplot(ceil(nMain/2), 2, i)
    boxplot(mainScores(:,i), relation_cat)
    title(['Relation – ' mainCatNames_unique{i}], 'FontWeight','bold')
    ylabel('Score')
    ylim([1 10])
  
        text(1, 2, mainP_relation(i), 'HorizontalAlignment','left','FontWeight','bold')

  end
sgtitle('Main Categories – Relation', 'FontSize', 16, 'FontWeight','bold');
saveFig(h, baseName, 'Main_Relation');

%% SUB × GENDER
h = figure('Color','w','Position',[200 200 1800 1200]);
for i = 1:nSub
    subplot(ceil(nSub/4), 4, i)
    boxplot(subScores(:,i), gender_cat)
    title(subCatNames_unique{i}, 'FontWeight','bold')
    ylabel('Score')
    ylim([1 10])

        text(1.5, 2, subP_gender(i), 'HorizontalAlignment','center','FontWeight','bold')
    
end
sgtitle('Subcategories – Gender', 'FontSize', 16, 'FontWeight','bold');
saveFig(h, baseName, 'Sub_Gender');

%% SUB × INSTITUTION
h = figure('Color','w','Position',[200 200 1800 1200]);
for i = 1:nSub
    subplot(ceil(nSub/4), 4, i)
    boxplot(subScores(:,i), inst_cat)
    title(['Institution – ' subCatNames_unique{i}], 'FontWeight','bold')
    ylabel('Score')
    ylim([1 10])

        text(1, 2, subP_institution(i), 'HorizontalAlignment','left','FontWeight','bold')
  
end
sgtitle('Subcategories – Institution', 'FontSize', 16, 'FontWeight','bold');
saveFig(h, baseName, 'Sub_Institution');

%% SUB × RELATION
h = figure('Color','w','Position',[200 200 1800 1200]);
for i = 1:nSub
    subplot(ceil(nSub/4), 4, i)
    boxplot(subScores(:,i), relation_cat)
    title(['Relation – ' subCatNames_unique{i}], 'FontWeight','bold')
    ylabel('Score')
    ylim([1 10])
  
        text(1, 2, subP_relation(i), 'HorizontalAlignment','left','FontWeight','bold')
   
end
    sgtitle('Subcategories – Relation', 'FontSize', 16, 'FontWeight','bold');
    saveFig(h, baseName, 'Sub_Relation');

    %% ============================================================
    % 5. MIXED-EFFECTS REGRESSION (QUESTION-LEVEL DATA)
    % ============================================================

    %% LONG-FORM DATA – MAIN
    Main_Long = table();
    row = 1;

    for c = 1:nMain
        catName = mainCatNames_unique{c};
        cols = find(strcmp(mainCats, catName));

        for q = cols
            for i = 1:nObs
                Main_Long.Participant(row,1) = i;
                Main_Long.Question(row,1)    = q;
                Main_Long.Score(row,1)       = numericData(i,q);
                Main_Long.Institution(row,1) = inst_cat(i);
                Main_Long.Relation(row,1)    = relation_cat(i);
                Main_Long.Gender(row,1)      = gender_cat(i);
                Main_Long.Category(row,1)    = string(catName);
                row = row + 1;
            end
        end
    end

    %% LONG-FORM DATA – SUB
    Sub_Long = table();
    row = 1;

    for c = 1:nSub
        catName = subCatNames_unique{c};
        cols = find(strcmp(subCats, catName));

        for q = cols
            for i = 1:nObs
                Sub_Long.Participant(row,1) = i;
                Sub_Long.Question(row,1)    = q;
                Sub_Long.Score(row,1)       = numericData(i,q);
                Sub_Long.Institution(row,1) = inst_cat(i);
                Sub_Long.Relation(row,1)    = relation_cat(i);
                Sub_Long.Gender(row,1)      = gender_cat(i);
                Sub_Long.Category(row,1)    = string(catName);
                row = row + 1;
            end
        end
    end

    %% MIXED-EFFECTS – MAIN (adaptive, never empty)
    Main_Reg_Results = table();
    row = 1;

    for c = 1:nMain
        catName = mainCatNames_unique{c};
        T = Main_Long(Main_Long.Category == catName, :);

        % Candidate predictors
        predictors = {};
        if numel(categories(T.Institution)) >= 2, predictors{end+1} = 'Institution'; end
        if numel(categories(T.Relation))    >= 2, predictors{end+1} = 'Relation';    end
        if numel(categories(T.Gender))      >= 2, predictors{end+1} = 'Gender';      end

        if isempty(predictors)
            continue
        end

        % Try models from full → reduced
        modelFitted = false;

        for k = numel(predictors):-1:1
            combos = nchoosek(1:numel(predictors), k);

            for j = 1:size(combos,1)
                predSet = predictors(combos(j,:));
                fixedPart = strjoin(predSet, ' + ');
                formula = sprintf('Score ~ %s + (1|Participant) + (1|Question)', fixedPart);

                try
                    lme = fitlme(T, formula);
                    modelFitted = true;
                    break
                catch
                    % try next combination
                end
            end

            if modelFitted
                break
            end
        end

        if ~modelFitted
            continue
        end

        coeffs = lme.Coefficients;

        for k = 2:height(coeffs)
            Main_Reg_Results.Category(row,1)   = string(catName);
            Main_Reg_Results.Predictor(row,1)  = string(coeffs.Name{k});
            Main_Reg_Results.Estimate(row,1)   = coeffs.Estimate(k);
            Main_Reg_Results.SE(row,1)         = coeffs.SE(k);
            Main_Reg_Results.tStat(row,1)      = coeffs.tStat(k);
            Main_Reg_Results.pValue(row,1)     = coeffs.pValue(k);
            row = row + 1;
        end
    end

    %% MIXED-EFFECTS – SUB (adaptive, never empty)
    Sub_Reg_Results = table();
    row = 1;

    for c = 1:nSub
        catName = subCatNames_unique{c};
        T = Sub_Long(Sub_Long.Category == catName, :);

        predictors = {};
        if numel(categories(T.Institution)) >= 2, predictors{end+1} = 'Institution'; end
        if numel(categories(T.Relation))    >= 2, predictors{end+1} = 'Relation';    end
        if numel(categories(T.Gender))      >= 2, predictors{end+1} = 'Gender';      end

        if isempty(predictors)
            continue
        end

        modelFitted = false;

        for k = numel(predictors):-1:1
            combos = nchoosek(1:numel(predictors), k);

            for j = 1:size(combos,1)
                predSet = predictors(combos(j,:));
                fixedPart = strjoin(predSet, ' + ');
                formula = sprintf('Score ~ %s + (1|Participant) + (1|Question)', fixedPart);

                try
                    lme = fitlme(T, formula);
                    modelFitted = true;
                    break
                catch
                end
            end

            if modelFitted
                break
            end
        end

        if ~modelFitted
            continue
        end

        coeffs = lme.Coefficients;

        for k = 2:height(coeffs)
            Sub_Reg_Results.Category(row,1)   = string(catName);
            Sub_Reg_Results.Predictor(row,1)  = string(coeffs.Name{k});
            Sub_Reg_Results.Estimate(row,1)   = coeffs.Estimate(k);
            Sub_Reg_Results.SE(row,1)         = coeffs.SE(k);
            Sub_Reg_Results.tStat(row,1)      = coeffs.tStat(k);
            Sub_Reg_Results.pValue(row,1)     = coeffs.pValue(k);
            row = row + 1;
        end
    end
   
    %% ============================================================
% DESCRIPTIVE STATISTICS FOR COVARIATES
% ============================================================

% Helper to compute frequency + percentage
covDesc = @(catVar, name) ...
    table( ...
        repmat(string(name), numel(categories(catVar)), 1), ...
        categories(catVar), ...
        countcats(catVar), ...
        round(100 * countcats(catVar) / numel(catVar), 2), ...
        'VariableNames', {'Covariate','Level','Count','Percent'} ...
    );

% Compute descriptives for each covariate
T_gender     = covDesc(gender_cat,   'Gender');
T_institution = covDesc(inst_cat,    'Institution');
T_relation    = covDesc(relation_cat,'Relation');

% Combine into one table
Covariate_Descriptives = [
    T_gender;
    T_institution;
    T_relation
];

% Save to Excel
excel_cov = sprintf('%s_ALTAI_stats.xlsx', baseName);
writetable(Covariate_Descriptives, excel_cov, 'Sheet','Covariate_Descriptives');
    
    %% ------------------------------------------------------------
    % 6. EXPORT ALL RESULTS
    % ------------------------------------------------------------
    excel_np  = sprintf('%s_ALTAI_stats.xlsx',            baseName);
    excel_reg = sprintf('%s_mixed_effects_regression.xlsx', baseName);

    writetable(MainCategoryStats, excel_np,  'Sheet','Main');
    writetable(SubCategoryStats,  excel_np,  'Sheet','Sub');

    writetable(Main_Reg_Results,  excel_reg, 'Sheet','Main');
    writetable(Sub_Reg_Results,   excel_reg, 'Sheet','Sub');
end
    function saveFig(h, baseName, tag)
        % Save MATLAB figure (.fig)
        savefig(h, sprintf('%s_%s.fig', baseName, tag));

        % Save high-resolution PNG
        saveas(h, sprintf('%s_%s.png', baseName, tag));
    end
