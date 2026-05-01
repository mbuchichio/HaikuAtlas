class BWindow : public BLooper {
public:
								BWindow(BRect frame, const char* title,
									window_type type, uint32 flags,
									uint32 workspace = B_CURRENT_WORKSPACE);
	virtual						~BWindow();

	static	BArchivable*		Instantiate(BMessage* archive);
	virtual	status_t			Archive(BMessage* archive,
									bool deep = true) const;

	virtual	void				Quit();
			void				Close() { Quit(); }
	virtual	void				MessageReceived(BMessage* message);
	virtual	void				FrameResized(float newWidth, float newHeight);

private:
	virtual	void				_ReservedWindow1();
};
