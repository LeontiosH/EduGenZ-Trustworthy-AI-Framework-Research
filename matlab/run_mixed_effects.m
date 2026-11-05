function run_mixed_effects(repoRoot)
% Refit the supplied adaptive mixed-effects procedure from de-identified CSV.
% MATLAB R2026a; Statistics and Machine Learning Toolbox.
if nargin < 1, repoRoot=fileparts(fileparts(mfilename('fullpath'))); end
if ~isfile(fullfile(repoRoot,'data','responses.csv'))
    error('EduGenZ:DataEmbargo','Participant-level data are not included in this public release. See docs/DATA_ACCESS.md.');
end
out=fullfile(repoRoot,'results','mixed_effects');
if ~isfolder(out), mkdir(out); end
diary(fullfile(out,'fit_log.txt'));
cleanup=onCleanup(@() diary('off')); %#ok<NASGU>
D=readtable(fullfile(repoRoot,'data','responses.csv'),'TextType','string');
I=readtable(fullfile(repoRoot,'data','item_dictionary.csv'),'TextType','string');
X=D{:,5:88};
assert(isequal(size(X),[87 84]) && all(ismember(X(:),0:3)));
X(X==0)=NaN;
inst=categorical(D.institution); role=categorical(D.project_role); gender=categorical(D.gender);
for level=1:2
    if level==1
        headers=I.requirement_code; stem='requirements';
    else
        headers=I.subcategory_source_code; stem='subcategories';
    end
    codes=unique(headers,'stable'); records=table(); coefficients=table();
    for c=1:numel(codes)
        code=codes(c); cols=find(headers==code);
        part=repmat((1:87)',numel(cols),1);
        question=repelem(cols,87); scores=reshape(X(:,cols),[],1);
        T=table(part,question,scores,inst(part),role(part),gender(part),...
            'VariableNames',{'Participant','Question','Score','Institution','Relation','Gender'});
        predictors={};
        if numel(categories(T.Institution))>=2, predictors{end+1}='Institution'; end
        if numel(categories(T.Relation))>=2, predictors{end+1}='Relation'; end
        if numel(categories(T.Gender))>=2, predictors{end+1}='Gender'; end
        fitted=false; formula=''; tried=0; lastError="";
        for k=numel(predictors):-1:1
            combos=nchoosek(1:numel(predictors),k);
            for j=1:size(combos,1)
                predSet=predictors(combos(j,:)); tried=tried+1;
                formula=sprintf('Score ~ %s + (1|Participant) + (1|Question)',strjoin(predSet,' + '));
                fprintf('%s %s: %s\n',stem,code,formula);
                try
                    lme=fitlme(T,formula); fitted=true; break
                catch ME
                    lastError=string(ME.identifier)+": "+string(ME.message);
                    fprintf('Attempt failed: %s\n',lastError);
                end
            end
            if fitted, break; end
        end
        if fitted
            record=table(code,string(formula),tried,height(T),sum(isfinite(T.Score)),...
                'VariableNames',{'Category','Formula','Attempts','RowsIncludingExcluded','NonzeroRatings'});
            records=[records;record]; %#ok<AGROW>
            C=lme.Coefficients;
            if isa(C,'dataset'), C=dataset2table(C); end
            C=addvars(C,repmat(code,height(C),1),'Before',1,'NewVariableNames','Category');
            coefficients=[coefficients;C]; %#ok<AGROW>
            save(fullfile(out,[stem '_' char(code) '_model.mat']),'lme','formula','predSet');
        else
            fprintf('No model fitted for %s; final error: %s\n',code,lastError);
        end
    end
    writetable(records,fullfile(out,[stem '_model_specifications.csv']));
    writetable(coefficients,fullfile(out,[stem '_coefficients_all.csv']));
end
fprintf('Mixed-effects output: %s\n',out);
end
