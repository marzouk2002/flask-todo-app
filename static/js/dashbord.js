const listsContainer = $("[data-lists]")
const listForm = $("[data-new-list-form]")
const listTitle = $("[data-list-title]")
const listCount = $("[data-list-count]")
const tasksContainer = $("[data-tasks]")
const listDelete = $('[data-delete-list-button]')
const clearTask = $('[data-clear-complete-tasks-button]')
const taskTemplate = document.querySelector('#task-template')

function Initializer() {
    fetch('/getlists')
        .then(res => res.json())
        .then(data => {
            displayLists(data.lists)
            selectList()
        })
}

function displayLists(lists) {
    $(listTitle).text('Select a list')
    $(listCount).text('')
    $(tasksContainer).html('')
    $('[data-new-task-input]').val('')
    localStorage.removeItem('current-list')
    let str=''
    lists.forEach((list) => {
        const strToadd = `<li data-list_id=${list.id} class="list-name">${list.title}</li>`
        str += strToadd
    });
    $(listsContainer).html(str)
}

function selectList() {
    const lists = $('.list-name').toArray()
    $.each(lists, ( index,list)=> {
        $(list).click(()=> {
            $.each(lists, (i,li)=>{
                $(li).removeClass('active-list')
            })
            const title = list.innerText
            const id = list.dataset.list_id
            $(listTitle).text(title)
            $(list).addClass('active-list')
            localStorage.setItem('current-list', id)
            fetchTasks(id)
        })
    })
}

function fetchTasks(list_id) {
    fetch(`/gettask/${list_id}`)
        .then(res => res.json())
        .then(data => {
            $(tasksContainer).html('')
            displayTasks(data.tasks)
        })
}

function displayTasks(tasks) {
    $(tasksContainer).html('')
    $('[data-new-task-input]').val('')
    let count=0
    tasks.forEach(task => {
        const taskStatus = Boolean(task.status)
        const taskElement = document.importNode(taskTemplate.content, true)
        const checkbox = taskElement.querySelector('input')
        checkbox.id = task.id
        checkbox.checked = taskStatus
        count = taskStatus ? count : count+1
        const label = taskElement.querySelector('label')
        label.htmlFor = task.id
        label.append(task.content)
        const list_id = localStorage.getItem('current-list')
        checkbox.addEventListener( 'click',() => {
            fetch('/task', {
                method:'PUT',
                body : JSON.stringify({task_id: task.id, list_id:list_id}),
                headers: {
                    'Content-Type': 'application/json'}
            })
            .then(res => res.json())
            .then(data => {
                $(listCount).text(`${data.counter} tasks remaining`)
            })
        })
        $(tasksContainer).append(taskElement)
    })
    $(listCount).text(`${count} tasks remaining`)
}

function deleteList() {
    const list_id = localStorage.getItem('current-list')
    if (!list_id) return
    fetch('/list', {
        method: 'DELETE',
        body: JSON.stringify({list_id}),
        headers: {
            'Content-Type': 'application/json'}
    }).then(res => res.json())
        .then(data => {
            displayLists(data.lists)
            selectList()
        })
}

function deleteDoneTasks() {
    const list_id = localStorage.getItem('current-list')
    if (!list_id) return
    fetch('/cleartask', {
        method: 'DELETE',
        body: JSON.stringify({list_id}),
        headers: {
            'Content-Type': 'application/json'}
    }).then(res => res.json())
    .then(data => {
        displayTasks(data.tasks)
    })
}

$(listForm).submit((e)=> {
    e.preventDefault()
    const title = $('[data-new-list-input]').val()

    if(title == '') return
    
    fetch('/list', {
        method: 'POST',
        body: JSON.stringify({list_title: title}),
        headers: {
            'Content-Type': 'application/json'}
    }).then(res => res.json())
        .then(data => {
            displayLists(data.lists)
            selectList()
            $('[data-new-list-input]').val('')
        })
})

$("[data-new-task-form]").submit((e) => {
    e.preventDefault()

    const task = $('[data-new-task-input]').val()
    $('[data-new-task-input]').val('')
    const list_id = localStorage.getItem('current-list')
    if(!task && !list_id) return
    fetch('/task', {
        method: 'POST',
        body: JSON.stringify({list_id, content: task}),
        headers: {
            'Content-Type': 'application/json'}
    }).then(res => res.json())
    .then(data => {
        $(tasksContainer).html('')
        displayTasks(data.tasks)
    })

})

$("[data-logout]").click(()=>{
    localStorage.removeItem('current-list')
})

$(listDelete).click(deleteList)

$(clearTask).click(deleteDoneTasks)

Initializer()