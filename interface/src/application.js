
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

class ModesSelect extends React.Component {
    constructor(props) {
        super(props);
        this.state = {mode: props.initialMode};
    }

    modeUpdate(event) {
        let newMode = event.target.innerText || event.target.value;
        this.props.modeUpdate(newMode);
        this.setState({mode: newMode});
    }

    cycle(event) {
        let arr = this.props.modes.concat(this.props.modes);
        let newMode = arr[arr.indexOf(this.state.mode) + 1];
        this.props.modeUpdate(newMode);
        this.setState({mode: newMode});
    }

    render() {
        let name = new String(Math.random());
        return [<span style={{'cursor': 'e-resize', 'userSelect': 'none'}}
                        onClick={(event) => this.cycle(event)}>{this.props.label}:</span>].concat(this.props.modes .map (
            (value) => <span onClick={(event) => this.modeUpdate(event)} style={{'cursor': 'default', 'userSelect': 'none'}}>
                <input type="radio" name={name} value={value} checked={value === this.state.mode}
                        onChange={(event) => this.modeUpdate(event)}></input>
                {value}
            </span>
        ));
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

        if (action1[action1.length - 1] === 1) {
            console.log("EXO", action1);
        }

        if (lockedButtonsCount > 0) {
            action(action1, doAction);
        }
    }

    doAction();
}

let codesDisplayMode = "show";
let codesModeUpdate = (newMode) => {
    codesDisplayMode = newMode;
    colorEncodingsTransparent = {}; 
    setTimeout(frameRender, 10);
};
ReactDOM.render(<ModesSelect modes={["none", "show"]} label="Codes"
                                initialMode={codesDisplayMode} modeUpdate={codesModeUpdate} />,
                document.getElementById('codes-display-modes-selection'));


let blocksDisplayMode = "translucent";
let blocksModeUpdate = (newMode) => {
    blocksDisplayMode = newMode;
    colorEncodingsTransparent = {};
    setTimeout(frameRender, 10);
}
ReactDOM.render(<ModesSelect modes={["none", "translucent", "solid"]} label="Blocks"
                                initialMode={blocksDisplayMode} modeUpdate={blocksModeUpdate} />,
                document.getElementById('blocks-display-modes-selection'));


let downloadId = new String(Math.random()).substring(2);
ReactDOM.render([<DownloadsSelection id={downloadId} values={[".mp4 Replay Video", ".bk2 Replay Data", ".json Action Sequence"]}
                                        initialValue=".mp4 Replay Video" />,
                    <span>&nbsp;</span>,
                    <button onClick={(event) => download(document.getElementById(downloadId).value, event)}>Download</button>],
                document.querySelector('.downloads-selection'));

class DataDisplay extends React.Component {
    render() {
        if (this.props.data.length > 0) {
            return <div className="data-display">
                {this.props.data .map ( ({Type: type, Value: value, Shape: shape, Elements: elements, ...obj}) => {

                    if (type === "Image") {
                        return <div style={{position: 'relative', display: 'inline-block'}}>
                            <img src={value} style={{imageRendering: 'pixelated'}} height={shape[0]} width={shape[1]} />

                            { elements .map ( ({Type: type, Geometry: [[x1, y1], [x2, y2]], Color: [r, g, b, a]}) => {
                                return <span style={{position: 'absolute',
                                                        left: x1, top: y1,
                                                        width: x2 - x1,
                                                        height: y2 - y1,
                                                        background: `rgba(${r*255}, ${g*255}, ${b*255}, ${a})`}}></span>
                            } ) }
                        </div>;
                    } else if (type === "Number") {
                        return <span className="number">{value}</span>;
                    } else if (type === "Array2D") {
                        let rowText = (row) => `[${row}]`;

                        let clipboardText = `np.array([\n${value .map (rowText) .join(",\n")}])`;
                        value = value.concat([Array(value[0].length).fill(" ")]);

                        value[value.length - 1][value[0].length - 1] = <span className="clipboard-button" title="Copy to Clipboard" onClick={(event) => clipboardCopy(clipboardText, event)}>📋</span>;

                        return <table className="array">
                            <tbody>
                            {value .map ( row => <tr>{row .map (elem => <td>{elem}</td> )}</tr>)}
                            </tbody>
                        </table>;
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
    ReactDOM.render(<DataDisplay data={data}/>, document.getElementById('data-display-container'));
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

        frameRender(obs, encodings, frameIndex);
        blocksRender(blocks)
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

        frameRender(obs, encodings, frameIndex);
        blocksRender(blocks);

        /* */
        let {Data: data} = response;
        setDisplay(data);
    });
}

var canvas = document.getElementById("canvas");
var context = canvas.getContext("2d");
context.scale(3, 3);

var colorEncodings = {};
var colorEncodingsTransparent = {};

var consoleElement = document.getElementById('console');

function blocksRender(blocksUrls) {
    consoleElement.innerText = blocksUrls.length;

    var list = <div>
        {blocksUrls .map (url => <img key={url} src={url} />)}
    </div>;

    ReactDOM.render(list, document.getElementById('blocks'));
}

var lastFrame = null;
var lastEncodings = null;
var lastFrameIndex = null;
function frameRender(frame=lastFrame, encodings=lastEncodings, frameIndex=lastFrameIndex) {
    lastFrame = frame;
    lastEncodings = encodings;
    lastFrameIndex = frameIndex;

    var width = frame.length;
    var height = frame[0].length;

    var scale = 2.7;
    canvas.style.width = scale*width*8/7 + 'px';
    canvas.style.height = scale*width + 'px';

    for (var i = 0; i < width; i++) {
        for (var j = 0; j < height; j++) {
            context.beginPath();
            context.rect(j*2, i*2, 2, 2);
            context.fillStyle = 'rgb(' + frame[i][j].join(',') + ')';
            context.fill();
        }
    }

    var encodings = encodings.map(t => (t*10).toFixed(2)); 

    let blocksAlpha = {'none': 0, 'translucent': 0.3, 'solid': 1}[blocksDisplayMode];
    let codesAlpha = {'none': 0, 'show': 0.55}[codesDisplayMode];

    context.font = '12px serif';
    context.fillStyle = 'yellow';
    context.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    context.lineWidth = '0.1px';

    function hash(str, seed = 0) {
        // "Generate a Hash from string in Javascript"
        //    https://stackoverflow.com/a/52171480 
        let h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
        for (let i = 0, ch; i < str.length; i++) {
            ch = str.charCodeAt(i);
            h1 = Math.imul(h1 ^ ch, 2654435761);
            h2 = Math.imul(h2 ^ ch, 1597334677);
        }
        h1 = Math.imul(h1 ^ (h1>>>16), 2246822507) ^ Math.imul(h2 ^ (h2>>>13), 3266489909);
        h2 = Math.imul(h2 ^ (h2>>>16), 2246822507) ^ Math.imul(h1 ^ (h1>>>13), 3266489909);
        return 4294967296 * (2097151 & h2) + (h1>>>0);
    };

    /*let counts = {};
    for (var i = 0; i < 1000000; i++) {
        var code = Math.abs(hash(new String(Math.random()))) % 256;
        counts[code] = (counts[code] || 0) + 1;
    }
    document.getElementById('console1').innerText = JSON.stringify(counts);
    */

    var seed = "abcdefgh";
    for (var encoding of encodings) {
        var r = Math.abs(hash("red" + seed + new String(encoding))) % 256;
        var g = Math.abs(hash("green" + seed + new String(encoding))) % 256;
        var b = Math.abs(hash("blue" + seed + new String(encoding))) % 256;

        colorEncodings[encoding] = colorEncodings[encoding] || 'rgb(' + String([r, g, b]) + ')';
        colorEncodingsTransparent[encoding] = colorEncodingsTransparent[encoding] || 'rgba(' + String([r, g, b, blocksAlpha]) + ')';
    }

    var topChomp = 4;
    var bottomChomp = 2;

    var index = 0;
    var o = 16;
    for (var i = 0 + topChomp*16; i < width + 15 - bottomChomp*16; i+=16) {
        for (var j = 0; j < height; j+=16) {
            context.fillStyle = colorEncodingsTransparent[encodings[index]];
            context.beginPath();
            context.rect(j*2, i*2, 16*2, 16*2);
            context.fill();
            index += 1;
        }
    }

    index = 0;
    for (var i = 0 + topChomp*16; i < width + 15 - bottomChomp*16; i+=16) {
        for (var j = 0; j < height; j+=16) {
            context.fillStyle = `rgba(255, 255, 0, ${codesAlpha})`;
            context.fillText(encodings[index], j*2 + 5, i*2 + o + 4);
            // context.strokeText(encodings[index], j*2 + o / 2, i*2 + o);
            index += 1;
        }
    }

    // right-adjust frame index
    let frameIndexString = `${frameIndex}`;
    let textMetrics = context.measureText('_______'.substring(0, 7 - frameIndexString.length))
    context.fillStyle = 'yellow';
    context.fillText(frameIndexString, 2*width - 13 + textMetrics.width, 12);
}

reset("SuperMarioBros-Nes");