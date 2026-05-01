class BMessage {
public:
			uint32				what;

								BMessage();
								BMessage(uint32 what);
								BMessage(const BMessage& other);
	virtual						~BMessage();

			BMessage&			operator=(const BMessage& other);

			int32				CountNames(type_code type) const;
			bool				IsEmpty() const;
			void				PrintToStream() const;
			ssize_t				FlattenedSize() const;

private:
			void				_InitData();
};
