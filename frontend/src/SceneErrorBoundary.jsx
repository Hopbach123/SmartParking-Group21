import React from 'react';
export default class SceneErrorBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error('Spline scene failed', error, info); this.props.onFailure?.(error); }
  render() {
    if (this.state.error) return <div role="alert" style={{padding:24}}><strong>Không tải được mô hình Spline</strong><p>{String(this.state.error.message || this.state.error)}</p><p>Dashboard vẫn hoạt động. Kiểm tra mạng, WebGL và quyền public của scene.</p><button onClick={() => this.setState({error:null})}>Thử tải lại</button></div>;
    return this.props.children;
  }
}

