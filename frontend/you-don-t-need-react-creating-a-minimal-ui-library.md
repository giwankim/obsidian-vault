---
title: "You don't need React: creating a minimal UI library"
source: "https://pedroth.github.io/?p=post/NoNeedReact"
author:
published:
created: 2026-08-05
description:
tags:
  - "clippings"
---

> [!summary]
> A walkthrough of building a minimal UI library in roughly 60 lines of plain JavaScript that keeps the three things the author credits React for: immediate-mode rendering (UI as a function of state), HTML and JS unified in one language, and a reactive programming model.
> The whole library is a chainable `DomBuilder` wrapper over `document.createElement` plus a `useState` publish-subscribe helper that re-renders on change — no JSX, no virtual DOM, no build step.
> The React tutorial is then recreated with it: nested components, an async profile list, a task list, and tic-tac-toe with time-travel history, with the caveat that the author would not reach for this on large, complex projects.

**React** is an amazing library that revolutionized the way we build UIs (at least it is very popular). It popularized the idea of immediate mode UI programming (to a big audience), where the UI is a function of the state.

This enables us to build complex UIs in a simple way. We can use regular programming constructs like `ifs` and `loops` to render the UI, without worrying about details.

```js
// example of immediate mode UI pseudo-code
function renderUI(state) {
    if(state.loading) {
        return \`<div>Loading...</div>\`;
    }
    return \`
        <div>
            <h1>${state.title}</h1>
            <p>${state.description}</p>
            ${state.items.map(item => \`<li>${item}</li>\`).join("")}
        </div>
    \`;
}
```

The only potential issue with immediate mode is performance, since we need to re-render the entire UI on every state change. Still, there are many techniques to optimize this.

Besides the immediate mode, the other things that made **React** good, in my opinion, are the way it unites `html` with `js`, and the reactive programming model. But do these 3 concepts require such a big library? Can we do something similar with just a few lines of code? The answer is yes, and that’s what I want to show in this post. I will try to recreate the `React` tutorial with a minimal UI library.

In summary, we want three concepts in our minimal library:

- Immediate mode UI: the UI is a function of the state.
- Uniting `HTML` with `JS`, but we don't need new syntax — we can just use regular `JS` (which works perfectly fine).
- A simple reactive programming model, just a publish-subscribe mechanism applied to variables. From my understanding it could be something similar to **signals** in `Solid.js` or something from `RxJS`.

## Our minimal UI library

First we create our unification of `HTML` with `JS`. We want to be able to create DOM nodes in a composable way, without needing to write `document.createElement` all the time. We can create a simple wrapper around the DOM API that allows us to build complex DOM structures in a more readable way. Just like an `HTML` template, but in `JS`.

```js
const SVG_URL = "http://www.w3.org/2000/svg";
const SVG_TAGS = ["svg", "g", "circle", "ellipse", "line", "path", "polygon", "polyline", "rect"];

// Here it starts
class DomBuilder {
    constructor(element) { this.element = element; }
    attr(name, value = "") { this.element.setAttribute(name, value); return this; }
    style(styleStr) { this.element.setAttribute("style", styleStr); return this; }
    append(...elements) {
        elements.forEach(e => {
            if (!e) return;
            if (isElement(e)) {
                this.element.appendChild(e);
            } else if (isPromise(e)) {
                e.then(actualElem => this.append(actualElem));
            } else {
                this.element.appendChild(e.build());
            }
        })
        return this;
    }
    inner(value) {
        if (isPromise(value)) {
            value.then(v => this.element.innerHTML = v);
        } else {
            this.element.innerHTML = value;
        }
        return this;
    }
    removeChildren() {
        while (this.element.firstChild) { this.element.removeChild(this.element.lastChild); }
        return this;
    }
    event(eventName, lambda) { this.element.addEventListener(eventName, lambda); return this; }
    build() { return this.element; }
    addClass(className) {
        if (!className) return this;
        className.split(" ").filter(c => c).forEach(c => this.element.classList.add(c));
        return this;
    }
    static of(elem) {
        if (isElement(elem)) return new DomBuilder(elem);
        const isSvg = SVG_TAGS.includes(elem);
        const element = isSvg ? document.createElementNS(SVG_URL, elem) : document.createElement(elem);
        return new DomBuilder(element);
    }
    static ofId(id) { return new DomBuilder(document.getElementById(id)); }
}

// some utilities
function isElement(o) {
    return typeof HTMLElement === "object" ? o instanceof HTMLElement : o && typeof o === "object" && o !== null && o.nodeType === 1 && typeof o.nodeName === "string";
}
function isPromise(o) { return o instanceof Promise; }
```

The second step is to create the simple reactive programming model. We can create a simple `useState` function that allows us to create reactive variables. This is just a publish-subscribe mechanism, where we can subscribe to changes in the state and re-render the UI when the state changes.

```js
function useState(defaultState) {
    let state = defaultState;
    let onChangeLambda = [];
    const onChange = lambda => {
        onChangeLambda.push(lambda);
    }
    const setState = lambda => {
        state = lambda(state);
        onChangeLambda.forEach(func => {
            func(state)
        });
    }
    const getState = () => state;
    return [getState, setState, onChange];
}
```

The immediate mode UI comes naturally from `JS` functions and the other two concepts. We can just create a function that returns a `DomBuilder` and use the `useState` function to create reactive variables. When the state changes, we can re-render the UI by calling the function again.

## Recreating the React tutorial

Lets try to recreate the [`React` tutorial](https://react.dev/learn) with our minimal UI library. This will show how to use our library in practice.

## Creating nested components

Nested components

```html
<div id="nested"></div>
<script type="module">
    // Button component
    function MyButton(props) {
        return DomBuilder.of("button")
        .inner(\`I' am a ${props.name} button\`)
        .event("click", () => alert(\`Hello, from ${props.name}!\`));
    }

    // App component without state, just nested components
    function App() {
        return DomBuilder.of("div")
        .append(
            DomBuilder.of("h1")
            .style("color: black;")
            .inner("Welcome to our app"),
            MyButton({ name: "pedroth" })
        );
    }

    // Immediate mode implementation
    const root = DomBuilder.ofId("nested");
    root.append(App());
</script>
```

## Profile example

Profile example

```html
<div id="profile"></div>
<script type="module">

    const styles = {
        card: "border: 1px solid #ccc; padding: 10px; margin: 10px; border-radius: 8px;",
        cardName: "color: #333;",
        cardImage: "width: 100px; height: 100px; border-radius: 50%;",
    }

    async function getDataFromApi() {
        // Simulating an API call
        return new Promise(resolve => {
            setTimeout(() => {
                resolve([
                    { name: "Naruto", image: "posts/NoNeedReact/naruto_gpt.png" },
                    { name: "Kakashi", image: "posts/NoNeedReact/kakashi_gpt.png" },
                    { name: "Minato", image: "posts/NoNeedReact/minato_gpt.png" }
                ]);
            }, 3000);
        });
    }

    // Setting up state and fetching data
    const [getData, setData, onDataChange] = useState(null);
    getDataFromApi().then(data => setData(() => data));

    function profileCard(user) {
        return DomBuilder.of("div")
        .style(styles.card)
        .append(
            DomBuilder.of("h2")
            .style(styles.cardName)
            .inner(user.name),
            DomBuilder.of("img")
            .attr("src", user.image)
            .attr("alt", user.name)
            .style(styles.cardImage)
        );
    }

    function App() {
        const data = getData();

        if (!data) {
            return DomBuilder.of("h1")
            .style("color: #333;")
            .inner("Loading...");
        }

        return DomBuilder.of("div")
            .append(...data.map(user => profileCard(user)));
    }

    // Immediate mode implementation: re-render the entire UI on every state change
    const root = DomBuilder.ofId("profile");
    function render() {
        root.removeChildren()
        .append(App());
    }
    onDataChange(() => render());
    render();
</script>
```

## Task list example

Task list example

```html
<div id="tasks"></div>
<script type="module">

    const styles = {
        card: "border: 1px solid #ccc; padding: 10px; margin: 10px; border-radius: 8px;",
        taskRow: "display: flex; align-items: center; gap: 8px; margin-bottom: 6px;",
        taskDone: "text-decoration: line-through; color: #999;",
        taskPending: "color: #333;",
        taskInput: "flex: 1; padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px;",
        addButton: "padding: 6px 12px; border: none; background: #3b82f6; color: white; border-radius: 6px; cursor: pointer; font-size: 14px;",
    }

    // Setting up state
    const [getTasks, setTasks, onTasksChange] = useState([]);

    function Checkbox(task, index, tasks) {
        const checkbox = DomBuilder.of("input")
            .attr("type", "checkbox")
            .event("change", () => {
                const newTasks = [...tasks];
                newTasks[index].completed = !newTasks[index].completed;
                setTasks(() => newTasks);
            });
        // hack: accessing DOM element to change checked state.
        checkbox.element.checked = task.completed;
        return checkbox;
    }

    function TaskItem(task, index, tasks) {
        return DomBuilder.of("div")
            .style(styles.taskRow)
            .append(
                Checkbox(task, index, tasks),
                DomBuilder.of("span")
                .inner(task.title)
                .style(styles[task.completed ? "taskDone" : "taskPending"])
            );
    }

    function TextInput({ placeholder, onKeydown }) {
        return DomBuilder.of("input")
            .attr("type", "text")
            .attr("placeholder", placeholder)
            .style(styles.taskInput)
            .event("keydown", onKeydown);
    }

    function AddButton({ onClick }) {
        return DomBuilder.of("button")
            .inner("Add")
            .style(styles.addButton)
            .event("click", onClick);
    }

    function AddTaskInput() {
        function submit() {
            const title = input.element.value.trim();
            if (title) {
                setTasks(prev => [...prev, { title, completed: false }]);
                input.element.value = "";
            }
        }

        const input = TextInput({
            placeholder: "New task...",
            onKeydown: e => { if (e.key === "Enter") submit(); }
        });

        return DomBuilder.of("div")
            .style(styles.taskRow)
            .append(
                input,
                AddButton({ onClick: submit })
            );
    }

    function TaskList() {
        const tasks = getTasks();

        return DomBuilder.of("div")
        .append(
            DomBuilder.of("h1")
            .style("color: #333;")
            .inner("Task List"),
            AddTaskInput(),
            ...tasks.map((task, index) => TaskItem(task, index, tasks)),
        );
    }

    // immediate mode implementation: re-render the entire UI on every state change
    const root = DomBuilder.ofId("tasks");
    function render() {
        root.removeChildren()
        .append(TaskList());
    }
    onTasksChange(() => render());
    render();
</script>
```

## Tic tac toe example

Don't mind about game logic or styles, that part is given in react tutorial, just focus on the UI part, and how we can do it with our minimal library.

Tic tac toe example

```html
<style>
    #tic_tac_toe {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        text-align: center;
    }

    .status {
        margin-bottom: 20px;
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
    }

    .board-row {
        display: flex;
        justify-content: center;
    }

    .square {
        width: 80px;
        height: 80px;
        background: #fff;
        border: 2px solid #ddd;
        font-size: 2rem;
        font-weight: bold;
        line-height: 80px;
        margin: -1px;
        padding: 0;
        cursor: pointer;
        transition: background 0.2s;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .square:hover {
        background: #f9f9f9;
    }

    .square:focus {
        outline: none;
        background: #eef;
    }

    .reset-btn {
        margin-top: 20px;
        padding: 10px 20px;
        font-size: 1rem;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        transition: background 0.3s;
    }

    .reset-btn:hover {
        background-color: #0056b3;
    }
</style>
<div id="tic_tac_toe"></div>
<script type="module">
    // --- Tic-Tac-Toe Game Logic ---

    function calculateWinner(squares) {
        const lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], // rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8], // cols
            [0, 4, 8], [2, 4, 6]             // diagonals
        ];
        for (let i = 0; i < lines.length; i++) {
            const [a, b, c] = lines[i];
            if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
                return squares[a];
            }
        }
        return null;
    }

    // --- Components ---
    const [getGameState, setGameState, onGameUpdate] = useState({
        squares: Array(9).fill(null),
        xIsNext: true
    });

    function Square(i) {
        const value = getGameState().squares[i];
        return DomBuilder.of('button')
            .addClass('square')
            .inner(value || '')
            .event('click', () => handleClick(i));
    }

    function StatusDisplay() {
        const state = getGameState();
        const winner = calculateWinner(state.squares);

        let status;
        if (winner) {
            status = \`Winner: ${winner}\`;
        } else if (!state.squares.includes(null)) {
            status = "Draw!";
        } else {
            status = \`Next player: ${state.xIsNext ? 'X' : 'O'}\`;
        }

        return DomBuilder.of('div')
            .addClass('status')
            .inner(status);
    }

    function Board() {
        const board = DomBuilder.of('div');
        for (let r = 0; r < 3; r++) {
            const row = DomBuilder.of('div').addClass('board-row');
            for (let c = 0; c < 3; c++) {
                row.append(Square(r * 3 + c));
            }
            board.append(row);
        }
        return board;
    }

    function ResetButton() {
        return DomBuilder.of('button')
            .addClass('reset-btn')
            .inner('Reset Game')
            .event('click', () => {
                setGameState(() => ({
                    squares: Array(9).fill(null),
                    xIsNext: true
                }));
            });
    }

    function handleClick(i) {
        const state = getGameState();
        const squares = [...state.squares];

        if (calculateWinner(squares) || squares[i]) {
            return;
        }

        squares[i] = state.xIsNext ? 'X' : 'O';

        setGameState(prev => ({
            squares: squares,
            xIsNext: !prev.xIsNext
        }));
    }

    // Immediate mode implementation: re-render the entire UI on every state change
    function render() {
        const root = DomBuilder.ofId('tic_tac_toe').removeChildren();
        root.append(
            StatusDisplay(),
            Board(),
            ResetButton()
        );
    }
    onGameUpdate(() => render());
    render();

</script>
```

## Tic tac toe with time machine

With time machine

```html
<style>
#tic_tac_toe_time_machine {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    text-align: center;
    display: flex;
    flex-direction: row;
    gap: 2rem;
    align-items: flex-start;
}

.game-board {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.game-info {
    text-align: left;
    min-width: 150px;
    color: #333;
}

.status {
    margin-bottom: 20px;
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
}

.board-row {
    display: flex;
    justify-content: center;
}

.square {
    width: 80px;
    height: 80px;
    background: #fff;
    border: 2px solid #ddd;
    font-size: 2rem;
    font-weight: bold;
    line-height: 80px;
    margin: -1px;
    padding: 0;
    cursor: pointer;
    transition: background 0.2s;
    display: flex;
    justify-content: center;
    align-items: center;
}

.square:hover {
    background: #f9f9f9;
}

.square:focus {
    outline: none;
    background: #eef;
}

.reset-btn {
    margin-top: 20px;
    padding: 10px 20px;
    font-size: 1rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.3s;
}

.reset-btn:hover {
    background-color: #0056b3;
}

ol {
    padding-left: 30px;
}

li {
    margin-bottom: 8px;
}

.history-btn {
    background: #f8f9fa;
    border: 1px solid #ccc;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
}

.history-btn:hover {
    background: #e2e6ea;
}
</style>
<div id="tic_tac_toe_time_machine"></div>
<script type="module">
// --- Tic-Tac-Toe Game Logic ---

function calculateWinner(squares) {
    const lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], // rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], // cols
        [0, 4, 8], [2, 4, 6]             // diagonals
    ];
    for (let i = 0; i < lines.length; i++) {
        const [a, b, c] = lines[i];
        if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
            return squares[a];
        }
    }
    return null;
}

// --- Components ---

const [getGameState, setGameState, onGameUpdate] = useState({
    history: [{ squares: Array(9).fill(null) }],
    currentStep: 0,
    xIsNext: true
});

function Square(i) {
    const state = getGameState();
    const current = state.history[state.currentStep];
    const value = current.squares[i];

    return DomBuilder.of('button')
        .addClass('square')
        .inner(value || '')
        .event('click', () => handleClick(i));
}

function StatusDisplay() {
    const state = getGameState();
    const current = state.history[state.currentStep];
    const winner = calculateWinner(current.squares);

    let status;
    if (winner) {
        status = \`Winner: ${winner}\`;
    } else if (!current.squares.includes(null)) {
        status = "Draw!";
    } else {
        status = \`Next player: ${state.xIsNext ? 'X' : 'O'}\`;
    }

    return DomBuilder.of('div')
        .addClass('status')
        .inner(status);
}

function Board() {
    const board = DomBuilder.of('div');
    for (let r = 0; r < 3; r++) {
        const row = DomBuilder.of('div').addClass('board-row');
        for (let c = 0; c < 3; c++) {
            row.append(Square(r * 3 + c));
        }
        board.append(row);
    }
    return board;
}

function MoveList() {
    const state = getGameState();
    const moves = state.history.map((step, move) => {
        const desc = move ? \`Go to move #${move}\` : 'Go to game start';

        const btn = DomBuilder.of('button')
            .addClass('history-btn')
            .inner(desc)
            .event('click', () => jumpTo(move));

        return DomBuilder.of('li').append(btn);
    });

    return DomBuilder.of('ol').append(...moves);
}

function ResetButton() {
    return DomBuilder.of('button')
        .addClass('reset-btn')
        .inner('Reset Game')
        .event('click', () => {
            setGameState(() => ({
                history: [{ squares: Array(9).fill(null) }],
                currentStep: 0,
                xIsNext: true
            }));
        });
}

function jumpTo(step) {
    setGameState(prev => ({
        ...prev,
        currentStep: step,
        xIsNext: (step % 2) === 0
    }));
}

function handleClick(i) {
    const state = getGameState();
    const history = state.history.slice(0, state.currentStep + 1);
    const current = history[history.length - 1];
    const squares = [...current.squares];

    if (calculateWinner(squares) || squares[i]) {
        return;
    }

    squares[i] = state.xIsNext ? 'X' : 'O';

    setGameState(prev => ({
        history: history.concat([{ squares: squares }]),
        currentStep: history.length,
        xIsNext: !prev.xIsNext
    }));
}

function render() {
    const root = DomBuilder.ofId('tic_tac_toe_time_machine').removeChildren();

    const gameBoard = DomBuilder.of('div').addClass('game-board').append(
        StatusDisplay(),
        Board(),
        ResetButton()
    );

    const gameInfo = DomBuilder
        .of('div')
     .addClass('game-info')
     .append(
        DomBuilder
        .of('div')
        .inner("History"),
        MoveList()
    );
    root.append(gameBoard, gameInfo);
}

// Immediate mode implementation: re-render the entire UI on every state change
onGameUpdate(() => render());
render();
</script>
```

## Conclusion

The idea of this post was to show that we can create a minimal UI library, with functional components, reactive state, and a simple way to create DOM elements. This basically creates a immediate mode UI library, similar to `React`, but with a much smaller codebase.

Although this is useful for many purposes (I use it in my simple projects, including this site), I would not recommend for big complex projects, still it make sense to have an alternative. Hope you enjoyed the post!
