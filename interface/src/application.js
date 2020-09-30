
"🎲 ⚀ ⚁ ⚂ ⚃ ⚄ ⚅";

let clientId = new String(Math.random()).substring(2);

class GameSelection extends React.Component {
    render() {
        return <select defaultValue={this.props.selectedGame}
                        onChange={(event) => {/*this.setState({'selectedGame': event.target.value});*/ reset(event.target.value)}}> {
                this.props.gamesList .map (
                    (gameTitle) => <option value={gameTitle} key={gameTitle}>{gameTitle}</option>
                ) }
        </select>;
    }
}

class DownloadsSelection extends React.Component {
    render() {
        return <select id={this.props.id} defaultValue={this.props.initialValue}
                        onChange={(event) => this.props.onChange}> {
                this.props.values .map (
                    (value) => <option value={value} key={value}>{value}</option>
                ) }
        </select>;
    }
}

function query(request, process) {
    fetch('.', {
        method: 'POST',
        body: JSON.stringify(request)
    })
    .then(function(response) { return response.json(); })
    .then(process);
}

query({'Request': 'AvailableGames', 'ClientId': clientId}, function(response) {
    let games = response['AvailableGames'];
    ReactDOM.render(<GameSelection gamesList={games} selectedGame={"SuperMarioBros-Nes"}/>, document.querySelector('.title'));
});

let actionsMap = {
    'UP':        [0, 0, 0, 0, 1, 0, 0, 0, 0],
    'DOWN':      [0, 0, 0, 0, 0, 1, 0, 0, 0],
    'LEFT':      [0, 0, 0, 0, 0, 0, 1, 0, 0],
    'RIGHT':     [0, 0, 0, 0, 0, 0, 0, 1, 0],
    'NONE':      [0, 0, 0, 0, 0, 0, 0, 0, 0],
    'B':         [1, 0, 0, 0, 0, 0, 0, 0, 0],
    'A':         [0, 0, 0, 0, 0, 0, 0, 0, 1],
};

let lockedAction = actionsMap['NONE'];
let activeAction = actionsMap['NONE'];

function actionsAdd(action1, action2) {
    return action1 .map ((_, i) => Math.min(1, action1[i] + action2[i]))
}

function actionsSubtract(action1, action2) {
    return action1 .map ((_, i) => Math.max(0, action1[i] - action2[i]))
}

let lockedButtonsCount = 0;

let runIntervalId = null;

let controls = [...document.querySelectorAll('.controls button:not(.reset-button)')];
controls .map (function(button) {
    let buttonOnClick = button.onclick;
    button.onclick = null;

    let state = "Unpressed";
    let timeout = null;

    // todo: counterstates
    button.addEventListener("mousedown", function(event) {
        if (state === "Unpressed") {
            state = "Down";

            timeout = setTimeout(function() {
                if (state === "Down") {
                    state = "Locked";
                    lockedButtonsCount += 1;
                    lockedAction = actionsAdd(lockedAction, actionsMap[button.innerText]);
                    button.classList.add("control-locked");

                    if (lockedButtonsCount === 1) {
                        runContinuous();
                    }
                }
            }, 400);

        } else if (state === "Locked") {
            state = "Unpressed";
            lockedButtonsCount -= 1;
            button.classList.remove("control-locked");
            lockedAction = actionsSubtract(lockedAction, actionsMap[button.innerText]);
        }
    });

    button.addEventListener("mouseup", function(event) {
        if (state === "Down") {
            state = "Unpressed";
            activeAction = actionsMap[button.innerText];
            clearTimeout(timeout);

            if (lockedButtonsCount === 0) {
                buttonOnClick();
            } else {
                /*runContinuous();*/
            }
        }
    });
});

function runContinuous() {
    function doAction() {
        let action1 = actionsAdd(lockedAction, activeAction);
        activeAction = actionsMap['NONE'];

        if (lockedButtonsCount > 0) {
            action(action1, doAction);
        }
    }

    doAction();
}

let downloadId = new String(Math.random()).substring(2);
ReactDOM.render([<DownloadsSelection id={downloadId} values={[".mp4 Replay Video", ".bk2 Replay Data", ".json Action Sequence"]}
                                        initialValue=".mp4 Replay Video" />,
                    <span>&nbsp;</span>,
                    <button onClick={(event) => download(document.getElementById(downloadId).value, event)}>Download</button>],
                document.querySelector('.downloads-selection'));

class DataDisplay extends React.Component {
    shouldComponentUpdate() {
        return true;
    }

    render() {
        if (this.props.data.length > 0) {
            return <div className="data-display">
                {this.props.data .map ( ({Type: type, Value: value, Shape: shape, DisplayScale: displayScale, Elements: elements, ...obj}, mainIndex) => {

                    if (type === "Image") {
                        return <div key={mainIndex} style={{position: 'relative', display: 'inline-block'}}>
                            {this.props.isNested ?
                                <img key={value} src={value} style={{imageRendering: 'pixelated'}} height={displayScale*shape[0]} width={displayScale*shape[1]}></img>
                                :
                                <img src={value} style={{imageRendering: 'pixelated'}} height={displayScale*shape[0]} width={displayScale*shape[1]}></img> }

                            { elements .map ( ({Type: type,
                                                Geometry: [[x1, y1], [x2, y2]], Color: [r, g, b, a],
                                                Label: label, LabelColor: [r2, g2, b2, a2]}, index) => {

                                [x1, y1, x2, y2] = [displayScale*x1, displayScale*y1, displayScale*x2, displayScale*y2];

                                return <span key={`region-${index}`} style={{
                                                    position: 'absolute',
                                                    left: x1, top: y1,
                                                    width: x2 - x1,
                                                    height: y2 - y1,
                                                    fontSize: '0.5em',
                                                    overflow: 'hidden',

                                                    display: 'flex',
                                                    justifyContent: 'center',
                                                    alignItems: 'center',

                                                    background: `rgba(${r*255}, ${g*255}, ${b*255}, ${a})`,
                                                    color: `rgba(${r2*255}, ${g2*255}, ${b2*255}, ${a2})`}}>{label}</span>;
                            } ) }
                        </div>;
                    } else if (type === "Number") {
                        return <span key={mainIndex} className="number">{value}</span>;

                    } else if (type === "Array2D") {
                        let rowText = (row) => `[${row}]`;

                        let clipboardText = `np.array([\n${value .map (rowText) .join(",\n")}])`;
                        value = value.concat([Array(value[0].length).fill(" ")]);

                        value[value.length - 1][value[0].length - 1] = <span className="clipboard-button" title="Copy to Clipboard" onClick={(event) => clipboardCopy(clipboardText, event)}>📋</span>;

                        return <table key={mainIndex} className="array">
                            <tbody>
                            {value .map ( (row, i) => <tr key={i}>{row .map ((elem, j) => <td key={j}>{elem}</td> )}</tr>)}
                            </tbody>
                        </table>;
                    }
                    else if (type === "ForwardList") {
                        return <DataDisplay data={value} isNested={true} />;
                    }


                } )}
            </div>;
        } else {
            return <div></div>;
        }
    }
}

function clipboardCopy(text, event) {
    let element = document.getElementById('clipboard-input');
    element.style.visibility = 'visible';
    element.value = text;
    element.select();
    element.setSelectionRange(0, 99999);
    document.execCommand("copy");
    element.blur();
    element.style.visibility = 'hidden';

    event.target.classList.add('clipboard-clicked');
}

function setDisplay(data) {
    let dataDisplay = ReactDOM.render(<DataDisplay data={data}/>, document.getElementById('data-display-container'));
    // dataDisplay.forceUpdate();
}

var currentFrameIndex = 0;
function download(resourceType, event) {
    console.log('resourceType', resourceType);
    if (currentFrameIndex === 0) {
        return ;
    }

    let body = document.body;
    let element = event.target;
    element.classList.add("download-in-progress");
    body.classList.add("download-in-progress");
    element.disabled = true;

    query({
        "Request": "ResourceURL",
        "ResourceType": resourceType,
        "Game": lastSelectedGame,
        "ClientId": clientId
    }, function(fileUrl) {
        function onFileExists() {
            window.location = fileUrl;
            element.classList.remove("download-in-progress");
            body.classList.remove("download-in-progress");
            element.disabled = false;
        }

        let intervalId = setInterval(function() {
            fetch(fileUrl)
            .then(function() {
                clearInterval(intervalId);
                onFileExists();
            })
        }, 350);
    });
}

let lastSelectedGame = null;
function reset(game=lastSelectedGame) {
    lastSelectedGame = game;
    document.title = game;

    activeAction = actionsMap['NONE'];

    query({
        "Request": "Reset",
        "Game": game,
        "ClientId": clientId
    }, function(response) {
        let {Observation: obs,
                BlockEncodings: encodings,
                Blocks: blocks,
                FrameIndex: frameIndex} = response;

        currentFrameIndex = frameIndex;

        query({
            "Request": "ImageUrl",
            "ClientId": clientId
        }, function(faviconUrl) {
            let link = document.querySelector('head link');
            link.setAttribute('href', faviconUrl);
        });

        /* */
        let {Data: data} = response;
        setDisplay(data);
    });
}

var commitmentInterval = 6;
function action(action_, onResponse=function(){}) {
    query({
        "Request": "Action",
        "Action": action_,
        "CommitmentInterval": parseInt(commitmentInterval, 10),
        "ClientId": clientId
    }, function(response) {
        let {Observation: obs,
                BlockEncodings: encodings,
                Blocks: blocks,
                FrameIndex: frameIndex} = response;

        currentFrameIndex = frameIndex;

        onResponse();

        /* */
        let {Data: data} = response;
        setDisplay(data);
        
    });
}

reset("SuperMarioBros-Nes");