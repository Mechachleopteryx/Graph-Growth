function [ maxCliqueSize ] = cliqueSize( edges, varargin )
%CLIQUESIZE Summary of this function goes here
% Terminology:  clique is at least 3 nodes
    % clique is fully connected
        % every node has edge to every other node in clique
% This function calculates the maximum clique size

if length(varargin) >= 1
    currentCliqueSize = varargin{1};
else
    currentCliqueSize = 2;
end


numNodes = size(edges,1);
cliqueThisSize = 1;
while cliqueThisSize
    % Increment clique size counter
    currentCliqueSize = currentCliqueSize + 1;
    
    checkedCliques = struct('temp','temp');
    cliqueFound = 0;
    numCliquesChecked = 0;
    numTotalPossibleCliques = factorial(numNodes) / (factorial(currentCliqueSize)*factorial(numNodes-currentCliqueSize));
    fprintf('\nChecking %15.0f possible cliques of size %i\n',numTotalPossibleCliques,currentCliqueSize);
    fprintf('Checking clique ');
    while numCliquesChecked < ceil(0.5*numTotalPossibleCliques) && ~cliqueFound
        randomPossibleClique = randsample(numNodes,currentCliqueSize);
        randomPossibleClique = sort(randomPossibleClique');
        diveDownFields = checkedCliques;
        for k = 1:currentCliqueSize
            fieldName = ['c' num2str(randomPossibleClique(k))];
            if isfield(diveDownFields,fieldName)
                if k == currentCliqueSize
                    newClique = 0;
                    break;
                end
                diveDownFields = diveDownFields.(fieldName);
            else
                newClique = 1;
                break;
            end
        end
        
        if newClique
            numCliquesChecked = numCliquesChecked + 1;
            fprintf('%i',numCliquesChecked);
            lenCliStr = length(num2str(numCliquesChecked));
            % Add to checkedCliques
            strToEval = 'checkedCliques';
            for nodeIdx = 1:currentCliqueSize
                node = randomPossibleClique(nodeIdx);
                strToEval = [strToEval '.c' num2str(node)];
            end
            strToEval = [strToEval ' = 1;'];
            eval(strToEval);
            % Check that fully connected
            nodes = randomPossibleClique;
            fullyConnected = 1;
            for node1Idx = 1:currentCliqueSize
                node1 = nodes(node1Idx);
                for node2Idx = 1:currentCliqueSize
                    node2 = nodes(node2Idx);
                    if nodeIdx ~= node2Idx && node1 > node2
                        thisEdge = edges(node1, node2);
                        if thisEdge == 0
                            fullyConnected = 0;
                        end
                    end
                end
            end
            if fullyConnected
                cliqueFound = 1;
            end
            backSpaceStr = '';
            for bIdx = 1:lenCliStr
                backSpaceStr = [backSpaceStr '\b'];
            end
            fprintf(backSpaceStr);
        end
    end
    fprintf('\n');
    if ~cliqueFound
        fprintf('did NOT find a clique of size %i\n\n',currentCliqueSize);
        cliqueThisSize = 0;
    else
        fprintf('FOUND a clique of size %i\n\n',currentCliqueSize);
    end
end
maxCliqueSize = currentCliqueSize - 1;
end