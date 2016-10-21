class Home extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      categories: [],
      posts: [],
    };
  }

  componentDidMount() {
    $.getJSON('/api/categories/', categories => {
      this.setState({categories: categories});
    });

    $.getJSON('/api/posts/?parent_isnull=True', posts => {
      this.setState({posts: posts});
    });
  }

  _filterByCategory(categoryId) {
    $.getJSON(`/api/posts/?parent_isnull=True&category=${categoryId}`, posts => this.setState({posts: posts}));
  }

  render() {
    return (
      <div className="ui grid container">
        <div className="four wide column">
          <button className="fluid ui primary button">发表主题</button>
          <div className="ui large selection animated list">
            <div className="item">
              <i className="comment icon"></i>
              <div className="content">所有主题</div>
            </div>
            <div className="item">
              <i className="block layout icon"></i>
              <div className="content">所有分类</div>
            </div>
            <div className="ui divider"></div>
        {this.state.categories.map((category, i) => {
          return(
            <div key={i} className="item" onClick={this._filterByCategory.bind(this, category.id)}>
              <i className={(category.icon || 'square') + ' icon'}></i>
              <div className="content">{category.name}</div>
            </div>
          )
        })}
          </div>
        </div>

        <div className="twelve wide column">
          <div className="ui very relaxed list">
        {this.state.posts.map(post => {
          return(
            <div className="item">
              <img className="ui avatar image mini" src={post.author_gravatar}/>
              <div className="content">
              <h3 className="header"><a href={`posts/${post.id}/`}>{post.title}</a></h3>
              <div className="meta"><p>{post.created_at} 由 <strong>{post.author}</strong> 发表</p></div>
              <div className="description">{post.content}</div>
              </div>
            </div>
            )
          })
        }
          </div>
        </div>
      </div>
    );
  }
}

class ReplyList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      replies: [],
    };
  }

  componentDidMount() {
    let postId = this.props.postId;
    $.getJSON(`/api/posts/?parent=${postId}`, replies => {
      this.setState({replies: replies});
    });
  }
  render() {
    return (
      <div className="ui comments">
        {this.state.replies.map(post => {
          return(
            <div className="comment">
              <a className="avatar"><img className="ui avatar image mini" src={post.author_gravatar}/></a>
              <div className="content">
                <a className="author" href="#">{post.author}</a>
                <div className="metadata"><div className="date">{post.created_at} </div></div>
                <div className="text">{post.content}</div>
              </div>
            </div>
            )
          })
        }
      </div>
    );
  }
}

[Home, ReplyList].forEach( app => {
  let name = app.name.toLowerCase();
  if (document.getElementById(name)) {
    let dom = document.getElementById(name),
      props = dom.dataset;
    ReactDOM.render(React.createElement(app, props), dom);
  }
});