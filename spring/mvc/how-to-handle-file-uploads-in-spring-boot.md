---
title: "How to Handle File Uploads in Spring Boot"
source: "https://medium.com/@AlexanderObregon/how-to-handle-file-uploads-in-spring-boot-3c6ef8110c13"
author:
  - "[[Alexander Obregon]]"
published: 2026-10-16
created: 2026-10-19
description: "More"
tags:
  - "clippings"
---

> [!summary]
> Alexander Obregon builds a layered file-upload flow in Spring Boot: binding `MultipartFile` (or `List<MultipartFile>` for batches) with `@RequestParam`, and setting `spring.servlet.multipart.max-file-size` and `max-request-size` (defaults 1MB and 10MB) so oversized requests are rejected before controller code runs. Endpoint-specific validation sits on top, and because client filenames and content types are untrusted metadata, a dedicated `FileStorageService` writes each file under a server-generated UUID. A `@RestControllerAdvice` maps validation failures, `MaxUploadSizeExceededException`, and storage errors to 400, 413, and 500 without leaking I/O details to the client.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*o5FmjKTPdJTbhGE2MIjo6w.jpeg)

Image Source

File uploads begin with `MultipartFile`, though handling them well goes past accepting bytes from an HTTP request. We need to set size limits before oversized requests reach controller code, account for several files in the same request, check incoming metadata, treat client-provided names carefully, and keep permanent storage outside the controller. Spring Boot already configures multipart support for Spring MVC and exposes the main limits through application properties, while Spring Framework provides `MultipartFile` for reading uploaded content. From there, we can build a well-organized flow where the controller receives the request, validation checks the file, a storage service saves it, and error handling deals with failures in a consistent way.

*You can also check out my* [*Substack*](https://alexanderobregon.substack.com/)*, where I post more articles like this and keep a* [*Java/JVM section*](https://alexanderobregon.substack.com/s/java) *with related posts. I publish my weekly recaps there too!*

## Receiving Files in Spring Boot

Spring MVC can bind parts from a `multipart/form-data` request directly to `MultipartFile`, giving the controller access to uploaded content without manually parsing multipart boundaries. Spring Boot configures servlet multipart handling for a typical Spring MVC application, so receiving a file normally begins with a controller parameter rather than custom multipart infrastructure. At this stage, we can focus on how files enter the application, how large those requests are allowed to be, and how several files can arrive through the same endpoint.

### Receive a MultipartFile

To receive a single uploaded file, we can declare `MultipartFile` as a controller parameter and connect it to a named multipart field through `@RequestParam`. The field name sent by the client needs to match the annotation value so Spring MVC can associate that part with the correct parameter:

```rb
package com.example.uploads;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
public class FileUploadController {

    @PostMapping("/files")
    public ResponseEntity<String> upload(
            @RequestParam("file") MultipartFile file) {

        if (file.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body("File cannot be empty");
        }

        return ResponseEntity.ok(
                "Received " + file.getSize() + " bytes"
        );
    }
}
```

The multipart field named `file` becomes the `MultipartFile` passed into `upload`. Calling `isEmpty()` tells us that the submitted part contains no file data, while `getSize()` reports its size in bytes. `MultipartFile` also gives us methods such as `getContentType()`, `getOriginalFilename()`, `getInputStream()`, `getBytes()`, and `transferTo(Path)`, so later stages can inspect or copy the received content in the form that makes sense for the storage flow.

Spring treats uploaded content as request data rather than permanent storage. Depending on multipart configuration and the servlet container, content can remain in memory or move into temporary disk storage while the request is being handled. Anything the application needs after request handling finishes has to be copied to its intended destination later, which means `MultipartFile` represents the incoming upload rather than the final stored file.

The value inside `@RequestParam` also tells us what the client must send. With `@RequestParam("file")`, the multipart request needs a field named `file`. Spring MVC resolves that part before the controller body runs, allowing the method to receive a `MultipartFile` instead of dealing with raw multipart boundaries from the HTTP request.

Different `MultipartFile` methods serve different needs. `getBytes()` returns the entire upload as a byte array, while `getInputStream()` gives us a stream for reading the content. Basic information such as emptiness and byte count does not require reading the full file into memory first, so `isEmpty()` and `getSize()` are better choices when we only need information about the incoming part.

### Configure Upload Limits

Size boundaries belong in multipart configuration so Spring Boot and the servlet container can reject requests that exceed the allowed limits before regular controller handling continues. Spring Boot provides `spring.servlet.multipart.max-file-size` for an individual file and `spring.servlet.multipart.max-request-size` for the complete multipart request.

For a project that accepts files up to 10 MB while allowing up to 25 MB across the entire request, `application.properties` can contain:

```rb
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=25MB
```

The first property limits every uploaded file independently. The second applies to the complete multipart request, including all file parts and the rest of the multipart content. This means a request can remain below the individual file limit and still exceed the total request limit when several files arrive at the same time.

Spring Boot defaults to `1MB` for `max-file-size` and `10MB` for `max-request-size`. Smaller uploads can stay below those values during early development, while larger files expose the limits quickly. Keeping the intended values in configuration makes the accepted request sizes part of the application settings rather than leaving the only size check inside controller code.

Multipart configuration also includes `spring.servlet.multipart.file-size-threshold`, which defaults to `0B` and controls the threshold after which file content is written to disk during multipart handling. `spring.servlet.multipart.location` can provide an intermediate directory when the project needs a particular temporary location. These settings deal with request handling rather than the permanent destination where an accepted upload will eventually be stored.

Spring Boot keeps multipart support active by default through `spring.servlet.multipart.enabled`. For a regular Spring MVC application, we do not need to register an extra multipart library merely to receive `MultipartFile` parameters because Spring Boot configures multipart support around the servlet facilities already available to the application.

The individual file limit and total request limit should match what the endpoint is expected to receive. An endpoint accepting a single profile image can keep the total request limit relatively close to its per-file limit, while a batch endpoint needs enough request capacity for several accepted files along with multipart overhead.

### Accept Multiple Files

Several uploads can arrive through the same multipart field name, and Spring MVC can bind them to `List<MultipartFile>`. This gives us a single controller parameter for a batch of related files rather than requiring a different method parameter for every file that could arrive.

We can receive a batch through a multipart field named `files` like this:

```rb
package com.example.uploads;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
public class BatchUploadController {

    @PostMapping("/files/batch")
    public ResponseEntity<String> uploadFiles(
            @RequestParam("files") List<MultipartFile> files) {

        long nonEmptyFiles = files.stream()
                .filter(file -> !file.isEmpty())
                .count();

        return ResponseEntity.ok(
                "Received " + nonEmptyFiles + " non-empty files"
        );
    }
}
```

Spring MVC collects multipart parts named `files` and places them into the list passed to `uploadFiles`. We then receive every submitted `MultipartFile` in the collection, while the `isEmpty()` check prevents an empty part from being counted as actual file content.

Clients send several files by repeating the same multipart field name. From a terminal, the request can be sent like this:

```rb
curl -X POST http://localhost:8080/files/batch \
  -F "files=@report.pdf" \
  -F "files=@photo.png"
```

Both `-F` entries carry the field name `files`, which matches `@RequestParam("files")` in the controller. Spring MVC collects those parts before `uploadFiles` runs, so our controller receives the collection without parsing repeated multipart fields itself.

The total multipart request limit still applies across the entire batch. With a 10 MB `max-file-size` and a 25 MB `max-request-size`, three files close to 10 MB each can stay below the individual file boundary while exceeding the total request boundary. Batch endpoints therefore need both limits selected around the amount of data they are expected to receive.

Spring MVC can also bind uploaded files into `Map<String, MultipartFile>` or `MultiValueMap<String, MultipartFile>` when files arrive under different multipart field names. `List<MultipartFile>` remains a natural choice when several uploads belong to the same field, while the map forms are better suited to requests where different field names represent different file inputs.

## Building the Storage Flow

Receiving multipart data only gets the file into the application. Before anything is kept permanently, the upload should pass application rules, receive a server-generated storage name, and move through a dedicated service that owns filesystem operations. Keeping those responsibilities away from the controller gives the HTTP layer a narrower job, while validation and storage behavior can change without turning every upload endpoint into a large method.

### Check the Uploaded Data

Before a file reaches permanent storage, we can reject content that does not meet the rules for the endpoint. Spring Boot multipart limits already place an outer boundary around incoming requests, while application validation can apply more specific rules. An image endpoint, for instance, can accept a smaller size than the global multipart limit and restrict the declared media types to JPEG and PNG.

We can place those rules inside a dedicated component:

```rb
package com.example.uploads;

import java.util.Set;

import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class ImageUploadValidator {

    private static final long MAX_SIZE = 5 * 1024 * 1024;

    private static final Set<String> ALLOWED_TYPES =
            Set.of("image/jpeg", "image/png");

    public void validate(MultipartFile file) {
        if (file.isEmpty()) {
            throw new InvalidUploadException("File cannot be empty");
        }

        if (file.getSize() > MAX_SIZE) {
            throw new InvalidUploadException("File is too large");
        }

        String contentType = file.getContentType();

        if (contentType == null || !ALLOWED_TYPES.contains(contentType)) {
            throw new InvalidUploadException("File type is not accepted");
        }
    }
}
```

The first check rejects a multipart part with no file data, while the second places a 5 MB application rule around this particular upload. That value can be lower than the global Spring Boot multipart limit because the two limits apply at different stages. The final condition accepts only the declared media types allowed by this endpoint.

`getContentType()` returns the media type supplied with the multipart file. Because request metadata comes from the client, matching that value should not be treated as proof that the bytes truly belong to the claimed format. If the application needs file-format verification, the uploaded content can be read by a parser or detection library that recognizes the expected format before permanent storage.

The custom validation exception only needs to carry the reason the upload was rejected:

```rb
package com.example.uploads;

public class InvalidUploadException extends RuntimeException {

    public InvalidUploadException(String message) {
        super(message);
    }
}
```

Throwing a dedicated exception lets the validation component stop the upload without building an HTTP response itself. Status-code decisions can stay in centralized exception handling, while the validator remains focused on deciding if the incoming file meets the endpoint rules.

Validation can grow with the needs of the endpoint. Image dimensions, document structure, permitted extensions, or other file-specific rules can be checked before storage when those properties belong to the upload contract. The main boundary stays consistent, with validation deciding if the upload is acceptable and the storage component taking responsibility for accepted data.

### Treat File Names Safely

Client-provided filenames should be treated as metadata rather than trusted filesystem destinations. `MultipartFile.getOriginalFilename()` returns the name supplied by the client, and that value can contain directory information or sequences like `..`. Generating the stored name on the server keeps request data from deciding where a file is written.

A generated identifier can become the physical filename:

```rb
package com.example.uploads;

import java.util.UUID;

public final class StoredFileName {

    private StoredFileName() {
    }

    public static String create() {
        return UUID.randomUUID().toString();
    }
}
```

`UUID.randomUUID()` produces the value stored on disk, so an incoming filename such as `vacation.png` never becomes the filesystem destination. The original filename can still be retained as metadata if the application needs to display it later or associate it with a database record.

Leaving the extension off the generated storage name also avoids trusting an extension supplied by the client. If an extension is needed later, it can be derived after the file format has passed the rules established for that upload type. The original name and declared media type can remain metadata without controlling the physical filename.

Server-generated names also prevent duplicate client filenames from replacing each other accidentally. Two uploads can both arrive as `photo.png`, while each stored file receives its own generated identifier. The name shown to a user and the name stored on disk therefore do not need to be the same value.

### Move Storage Into a Service

Controllers stay easier to read when filesystem operations live in a dedicated service. The controller can receive the request, pass the file through validation, send accepted content to storage, and return an HTTP response. Directory creation, generated names, file transfer, and storage failures can remain inside the service.

A filesystem-backed service can keep its destination directory in application configuration:

```rb
package com.example.uploads;

import java.io.File;
import java.io.IOException;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class FileStorageService {

    private final File uploadDirectory;

    public FileStorageService(
            @Value("${app.upload.directory}") String uploadDirectory) {

        this.uploadDirectory =
                new File(uploadDirectory).getAbsoluteFile();
    }

    public String store(MultipartFile file) {
        try {
            prepareDirectory();

            String storedName = StoredFileName.create();
            File destination =
                    new File(uploadDirectory, storedName);

            file.transferTo(destination);

            return storedName;
        }
        catch (IOException ex) {
            throw new FileStorageException(
                    "Could not store uploaded file", ex
            );
        }
    }

    private void prepareDirectory() throws IOException {
        if (uploadDirectory.exists()) {
            if (!uploadDirectory.isDirectory()) {
                throw new IOException(
                        "Upload location is not a directory"
                );
            }

            return;
        }

        if (!uploadDirectory.mkdirs()) {
            throw new IOException(
                    "Could not create upload directory"
            );
        }
    }
}
```

The constructor turns the configured location into an absolute `File`, while `prepareDirectory()` checks that the location is a directory or creates it when it does not exist. After that, the service generates a server-controlled filename and passes the destination to `MultipartFile.transferTo(File)`, which transfers the received upload to that destination.

Because `StoredFileName.create()` returns a UUID value rather than client input, the destination filename does not carry directory traversal data from `getOriginalFilename()`. The service returns the generated name after the transfer finishes, giving the controller an application-level reference to the stored file.

The base directory can stay outside Java source code through `application.properties`:

```rb
app.upload.directory=uploads
```

Spring injects that value into the service constructor through `@Value`. Changing the destination then becomes a configuration change rather than a controller edit, and different environments can provide their own directory values through Spring configuration.

With validation and storage delegated, the controller becomes smaller:

```rb
package com.example.uploads;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
public class ImageUploadController {

    private final ImageUploadValidator validator;
    private final FileStorageService storageService;

    public ImageUploadController(
            ImageUploadValidator validator,
            FileStorageService storageService) {

        this.validator = validator;
        this.storageService = storageService;
    }

    @PostMapping("/images")
    public ResponseEntity<UploadResponse> uploadImage(
            @RequestParam("file") MultipartFile file) {

        validator.validate(file);

        String storedName = storageService.store(file);

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new UploadResponse(storedName));
    }

    record UploadResponse(String fileName) {
    }
}
```

The request enters through `MultipartFile`, then the controller sends it to `ImageUploadValidator` before calling `FileStorageService`. Successful storage returns the generated filename, which becomes part of the `201 Created` response. Filesystem details never enter the controller method, so the HTTP flow remains easy to follow as storage requirements grow.

This boundary also leaves room for a different storage implementation later. Local disk storage can be replaced by object storage or a different persistence mechanism while the controller continues sending accepted uploads to a storage service with the same responsibility. The HTTP endpoint does not need details about how the bytes reach their final destination.

### Return Upload Errors

Failures can happen at several points during an upload. Validation can reject empty or unsupported content, filesystem operations can fail, and multipart parsing can reject a request before the controller receives it if the configured size limit is exceeded. Central exception handling gives those failures consistent HTTP responses without adding repeated `try` and `catch` blocks to every upload controller.

Storage failures can carry their original I/O cause through a dedicated runtime exception:

```rb
package com.example.uploads;

public class FileStorageException extends RuntimeException {

    public FileStorageException(
            String message, Throwable cause) {

        super(message, cause);
    }
}
```

Wrapping `IOException` this way lets `FileStorageService` report that persistence failed without deciding which HTTP status the client should receive. That decision can stay at the web layer, where validation failures, multipart failures, and storage failures can all be translated into HTTP responses from the same location.

`@RestControllerAdvice` can handle those exceptions across REST controllers:

```rb
package com.example.uploads;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

@RestControllerAdvice
public class UploadExceptionHandler {

    @ExceptionHandler(InvalidUploadException.class)
    public ResponseEntity<String> handleInvalidUpload(
            InvalidUploadException ex) {

        return ResponseEntity.badRequest()
                .body(ex.getMessage());
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<String> handleMaximumSize(
            MaxUploadSizeExceededException ex) {

        return ResponseEntity.status(
                        HttpStatus.PAYLOAD_TOO_LARGE
                )
                .body("Upload exceeds the allowed size");
    }

    @ExceptionHandler(FileStorageException.class)
    public ResponseEntity<String> handleStorageFailure(
            FileStorageException ex) {

        return ResponseEntity.status(
                        HttpStatus.INTERNAL_SERVER_ERROR
                )
                .body("File could not be stored");
    }
}
```

`InvalidUploadException` becomes `400 Bad Request`, while an upload beyond the multipart maximum receives `413 Payload Too Large`. `FileStorageException` maps to `500 Internal Server Error` because the request reached storage but the server could not complete the write.

The response for a storage failure does not expose the underlying I/O exception text. Internal directory names or operating-system details do not belong in the client response, while the original exception can still remain attached to `FileStorageException` for server-side logging.

Size failures need different treatment from application validation because they can happen during multipart parsing before the controller method receives a `MultipartFile`. Controller-level `getSize()` checks therefore do not replace Spring Boot multipart limits. Configuration provides the outer request boundary, validation applies endpoint-specific rules after the request reaches application code, and centralized exception handling turns failures from both stages into HTTP responses.

## Conclusion

Spring Boot file uploads become much easier to manage when each responsibility stays in its own place. `MultipartFile` brings the request into the controller, multipart settings set the upload boundaries, validation checks the incoming data, generated names keep client filenames away from storage decisions, and a storage service handles the final write. Central exception handling then turns validation, size, and storage failures into consistent HTTP responses without filling the controller with repeated error logic.

**Thanks for reading! If you found this helpful, highlighting, clapping, or leaving a comment really helps me out.**

![](https://miro.medium.com/v2/resize:fit:1100/format:webp/1*7LCQHSwaBMSQIyaz83xAWg.png)

Spring Boot icon by Icons8
